def indent(n:int) -> str:
    if n == 0:
        return ''
    else:
        return '\n%*s'%(2*n, ' ')
