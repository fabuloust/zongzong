from utilities.enum import EnumBase, EnumItem


class SexChoices(EnumBase):
    """
    性别
    """
    MALE = EnumItem('m', u'男')
    FEMALE = EnumItem('f', u'女')
    UNKNOWN = EnumItem('u', u'未知')
