# coding=utf-8
import re
from ss_di import di


def mkfun(_from, _to, validate=False):
    """ V4.5 根据给定的_from容器和_to容器 (容器类型:list|set|tuple|dict|set)，返回一个遵循由_from到_to映射规则的函数(fun)
        参数validate：True则开启反向验证功能，默认False
        在返回的函数fun的说明文档中，o表示要转换的容器(p)，old表示原规则_to容器  @author:ss"""

    pattern1 = r'''(\w?'[^']*')|(\w?"[^"]*")'''  # 匹配带引号内容
    pattern2 = r'''(<[^,:]*>)|([^,:(){}[\] ]+)'''  # 匹配 <...> 和 其他

    b = str(_to)  # 最后执行的字符串
    b = re.sub(pattern1, '#', b)
    b = re.sub(pattern2, '#', b)

    _from_list = di(_from)  # _from的真实元素集中营
    _to_list = di(_to)  # _to的真实元素集中营

    for j, _to_object in enumerate(_to_list):
        replace_happened = False  # 是否发生替换
        for i, _from_object in enumerate(_from_list):
            if _to_object == _from_object:
                b = b.replace('#', 'o[' + str(i) + ']', 1)
                replace_happened = True
                break
        if not replace_happened:
            b = b.replace('#', 'old[' + str(j) + ']', 1)

    def f(p):
        old = _to_list  # eval中可能会访问的容器
        o = di(p)  # p的真实元素集中营
        return eval(b)

    f.__doc__ = '此函数为mkfun函数生成的转换函数（不验证）' \
                + '\n当前转换规则为： ' + str(_from) + ' -> ' + str(_to) \
                + '\n内部转换机制：' + b

    def f_with_validate(p):
        old = _to_list  # eval中可能会访问的容器
        o = di(p)
        result = eval(b)
        result_reverse = f_reverse(result)
        assert p == result_reverse, '转换没有通过反向验证！' \
                                    + '\n当前转换结果：' + str(p) + ' -> ' + str(result) \
                                    + '\n逆向转换结果：' + str(result) + ' -> ' + str(result_reverse)
        return result

    f_with_validate.__doc__ = '此函数为mkfun函数生成的转换函数（反向验证已开启）' \
                              + '\n当前转换规则为： ' + str(_from) + ' -> ' + str(_to) \
                              + '\n内部转换机制：' + b

    if validate:
        f_reverse = mkfun(_to, _from)
        return f_with_validate
    else:
        return f
