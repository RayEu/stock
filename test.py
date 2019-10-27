def check(fn):
    def inner(*args):
        data = args[0]
        cur_index = args[1]
        if cur_index <= 1:
            return False
        cur = data.loc[cur_index]
        pre = data.loc[cur_index - 1]
        ppre = data.loc[cur_index - 2]
        if cur.low < pre.low and cur.low < ppre.low:
            pass
        else:
            return False
        fn(data, cur_index)
    return inner


@check
def hammer_low(self, data, cur_index):
    first, second, third, fourth = self.pai_xu(data)
    if third - fourth >= (second - third) * 2 and first - second <= (second - third) * 0.5:
        return True
    else:
        return False


if __name__ == '__main__':
    a=A()
    b=B()
    c=C()
    for i in range(0, 10):
        b.cc()
        c.cc()
    print(a.token)