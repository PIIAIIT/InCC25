import re

def slugify(str):
    return re.sub(r"[',]", '',re.sub(r' ', '_', str))

def find_labels(instructions):
    labels = {}
    for pc, inst in enumerate(instructions):
        match inst:
            case 'label', name:
                labels[name] = pc
    return labels

def run(instructions, debug=False, detailed=False):
    
    labels    = find_labels(instructions)
    heap      = []
    variables = []
    stack     = []
    regs      = {}
    pc        = labels['main']

    def arg(x):
        if x in regs: return regs[x]
        elif x in labels: return labels[x]
        else: return x

    def state(detailed=False) :
        instruction = "" if pc >= len(instructions) else str(instructions[pc])
        if not detailed:
            return f'pc={pc:2d}, instr[pc]={instruction:30.30s}, variables={str(variables):10.10}, stack={str(stack):10.10}, heap={str(heap):10.10}, regs={regs}'
        return f'ICE-machine state:\n\tpc={pc:2d}\n\tinstr[pc]={instruction}\n\tvariables={str(variables)}\n\tstack={str(stack)}\n\theap={str(heap)}\n\tregs={regs}'
    
    while pc < len(instructions):
        print(state(detailed=detailed)) if debug else ""
        try:
            match instructions[pc]:
                case '+', res, arg1, arg2: regs[res] = arg(arg1) + arg(arg2)
                case '-', res, arg1, arg2: regs[res] = arg(arg1) - arg(arg2)
                case '*', res, arg1, arg2: regs[res] = arg(arg1) * arg(arg2)
                case '/', res, arg1, arg2: regs[res] = arg(arg1) // arg(arg2)
                case 'u-', res, arg1: regs[res] = -arg(arg1)
                case '<', res, arg1, arg2: regs[res] = arg(arg1) < arg(arg2)
                case '<=', res, arg1, arg2: regs[res] = arg(arg1) <= arg(arg2)
                case '==', res, arg1, arg2: regs[res] = arg(arg1) == arg(arg2)
                case '!=', res, arg1, arg2: regs[res] = arg(arg1) != arg(arg2)
                case '>=', res, arg1, arg2: regs[res] = arg(arg1) >= arg(arg2)
                case '>', res, arg1, arg2: regs[res] = arg(arg1) > arg(arg2)
                case 'and', res, arg1, arg2: regs[res] = arg(arg1) and arg(arg2)
                case 'or', res, arg1, arg2: regs[res] = arg(arg1) or arg(arg2)
                case 'not', res, arg1: regs[res] = not arg(arg1)
                case 'goto', name:
                    pc = labels[name]
                    continue
                case 'ifgoto', cond, name:
                    if regs[cond]:
                        pc = labels[name]
                        continue
                case '=', res, arg1:
                    regs[res] = arg(arg1)
                case 'comment', c: pass
                case 'label', l: pass
                case 'mk', ('i64'|'bool'), res, arg1:
                    heap.append(arg(arg1))
                    regs[res]=len(heap)-1
                case 'get', ty, res, arg1:
                    regs[res] = heap[arg(arg1)]
                case 'getvar', ty, res, arg1:
                    regs[res] = variables[arg(arg1)]
                case 'rewrite', ty, arg1, arg2:
                    heap[variables[arg1]] = heap[arg(arg2)]
                case 'enter', varvec_reg:
                    stack.append(variables)
                    variables = heap[regs[varvec_reg]]
                case 'fenter',varvec_reg:
                    stack.append(regs)
                    stack.append(variables)
                    variables = heap[regs[varvec_reg]]
                case 'leave',:
                    variables = stack.pop()
                case 'fleave',:
                    variables = stack.pop()
                    rval = regs['R0'] # rescue the return value from R0
                    regs = stack.pop()
                    regs['R0'] = rval  # and place rescued value
                case 'ret',:
                    pc = stack.pop()
                case 'mkvec', res, n:
                    heap.append([0]*n)
                    regs[res]=len(heap)-1
                case '[]=', vec, i, val:
                    heap[arg(vec)][i]=arg(val)
                case '=[]', res, vec, i:
                    regs[res] = heap[arg(vec)][i]
                case 'veccat', res, vec1, vec2:
                    heap.append(heap[arg(vec1)] + heap[arg(vec2)])
                    regs[res] = len(heap) - 1
                case 'showstate', *args:
                    print(state(detailed='detailed' in args))
                case 'call', fct:
                    stack.append(pc)
                    pc = arg(fct)
                    regs = dict()
                case _:
                    raise NotImplementedError(f'Unknown Instruction {instructions[pc]}')
        except Exception as e:
            print(f'ICE machine: {type(e)} occured in line {pc}: {tac_tupel_to_infix(instructions[pc])}')
            print(e)
            print(state(detailed=True))
        try:    
            pc += 1
        except Exception:
            print(pc)
    return regs


def writes(inst):
    match inst:
        case '+'|'-'|'*'|'/'|'<'|'>'|'<='|'=>'|'=='|'!=', r, _, _: return {r}
        case '[]=', vec, i, val: return {vec}
        case '=[]', res, vec, i: return {res}
        case 'veccat', res, vec1, vec2: return {res}
        case '='|'not'|'u-', r, _: return {r}
        case 'mk'|'get', _, r, _: return {r}
        case 'mkvec', r, _: return {r}
        case 'getvar', _, r, _: return {r}
        case 'label', _: return set()
        case 'comment', _: return set()
        case _: return set()


def reads(inst):
    is_register = lambda r : type(r) == str and r[0] == 'R'
    r = set()
    match inst:
        case'+'|'-'|'*'|'/'|'<'|'>'|'<='|'=>'|'=='|'!=', _, r1, r2:
            if is_register(r1): r.add(r1)
            if is_register(r2): r.add(r2)
        case '='|'not'|'u-', _, r1:
            if is_register(r1): r.add(r1)
        case 'mk'|'get', _, _, r1:
            if is_register(r1): r.add(r1)
        case 'ifgoto', r1, _:
            if is_register(r1): r.add(r1)
        case 'rewrite', _, _, r1:
            if is_register(r1): r.add(r1)
        case '[]=', vec, i, val: 
            if is_register(val): r.add(val)
            if is_register(vec): r.add(vec)
        case '=[]', res, vec, i:
            if is_register(vec): r.add(vec)
        case 'veccat', res, vec1, vec2:
            if is_register(vec1): r.add(vec1)
            if is_register(vec2): r.add(vec2)
        case 'enter', r1:
            if is_register(r1): r.add(r1)
        case 'fenter', r1:
            if is_register(r1): r.add(r1)
        case 'call', r1:
            if is_register(r1): r.add(r1)
        case 'ret',: r.add('R0')
        case 'label', _: pass
        case 'comment', _: pass
        case _: pass
    return r

def new_reg_type(line, current_reg_types):
    """
        ('type_i64:',   dq, '"i64    ",0'),
        ('type_ptr:',   dq, '"ptr    ",0'),
        ('type_vec:',   dq, '"vec    ",0'),
        ('type_vec_elt:',   dq, '"vecelt ",0'),
        ('type_fun:',   dq, '"fun    ",0'),
        ('type_other:', dq, '"other  ",0'),
        ('type_unknown:', dq, '"unknown",0'),
    """
    
    is_register = lambda r : type(r) == str and r[0] == 'R'
    match line:
        case'+'|'-'|'*'|'/'|'<'|'>'|'<='|'=>'|'=='|'!=', r, r1, _:
            return {r: current_reg_types[r1]} 
        case '='|'not'|'u-', r, r1:
            typ = 'type_i64' if isinstance(r1, int) else current_reg_types[r1] if r1 in current_reg_types else 'type_unknown'
            return {r: typ} 
            if is_register(r1): r.add(r1)
        case 'mk', typ, r, r1:
            return {r:'type_ptr'}
        case 'get', typ, r, r1:
            return {r: 'type_'+str(typ)}
        case '=[]', r, vec, i:
            return {r: 'type_vec_elt'}
        case 'veccat', r, vec1, vec2:
            return {r: 'type_ptr'}
        case _: pass
    return {}


class Inst(tuple):
    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls, args)

        for key, value in kwargs.items():
            setattr(obj, key, value)

        return obj


def reassign_registers(inst, reassignments):
    def arg(a):
        if a in reassignments: return reassignments[a]
        else: return a

    return Inst(*(arg(x) for x in inst), **inst.__dict__)


def tac_tupel_to_infix(l):
    def shorten(s, max_len=40):
        s=str(s)
        ellipsis = " [...]"
        if len(s) > max_len:
            return s[:max_len - len(ellipsis)] + ellipsis
        return s

    match l:
        case 'not', res, arg1: return f"{res} = not {arg1}"
        case 'goto', name: return f"goto {name}"
        case 'ifgoto', cond, name: return f"if {cond} goto {name}"
        case '=', res, arg1: return f"{res} = {arg1}"
        case 'not'|'u-' as op, res, arg1: return f"{res} = {op} {arg1}"
        case '[]=', array, idx, rhs: return f"{array}[{idx}] = {rhs}"
        case '=[]', lhs, vec, idx: return f"{lhs} = {vec}[{idx}]"
        case 'veccat', res, vec1, vec2: return f"{res} = veccat {vec1} {vec2}"
        case 'comment', c: return f"# {shorten(c)}"
        case 'label', l: return f"{l}:"
        case 'mk', type, res, arg1: return f"{res} = mk_{slugify(str(type))} {arg1}"
        case 'get', type, res, arg1: return f"{res} = get_{slugify(str(type))} {arg1}"
        case 'getvar', ty, res, arg1: return f'{res} = getvar_{ty} {arg1}'
        case 'rewrite', type, arg1, arg2: return f"rewrite_{slugify(str(type))} {arg1} {arg2}"
        case 'mkvec', ret, arg1: return f"{ret} = mkvec {arg1}"
        case 'showstate', *args: return f"showstate {args}"
        case 'ret',: return f"ret"
        case 'call', fun: return f"call {fun}"
        case 'enter', l: return f'enter {l}'
        case 'leave',: return 'leave'
        case 'fenter',: return f'fenter'
        case 'fenter',reg: return f'fenter {reg}'
        case 'fleave',: return f'fleave'
        case _ :
            if len(l) == 4:
                return str(l[1])+' = '+str(l[2])+' '+str(l[0])+' '+str(l[3])
            raise Exception(f"unknown ICE-Intermediate statement {l}")

        
if __name__ == "__main__":  
    run([
        ('=', 't1', 2),
        ('=', 't2', 4),
        ('+', 't3', 't1', 't2')
    ])
