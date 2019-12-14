from utilities.enum import EnumBase, EnumItem


class FootprintChoices(EnumBase):
    """
    活动类型
    """
    HELP = EnumItem(0, u'求帮忙')
    READ = EnumItem(1, u'读书')
    MOVIE = EnumItem(2, u'电影')
    TEA = EnumItem(3, u'下午茶')
    BAR = EnumItem(4, u'酒吧')
    FIT = EnumItem(5, u'健身')
    SHOPPING = EnumItem(6, u'逛街')


class CommentStatusChoices(EnumBase):
    """
    评论状态
    """
    NORMAL = EnumItem('n', u'正常')
    DELETED = EnumItem('d', u'已删除（用户自己或者管理员）')

