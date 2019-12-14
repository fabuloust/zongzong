from footprint.models import FootprintComment
from user_info.manager.user_info_mananger import get_user_info_db


def create_comment_db(comment_user, footprint_id, comment):

    user_info = get_user_info_db(comment_user)

    return FootprintComment.objects.create(footprint_id=footprint_id, comment=comment, nick_name=user_info.nickname,
                                           )


def comment_footprint(comment_user, footprint_id, comment):
    """
    评论某个痕迹，后续可能需要加入敏感词控制
    """
    create_comment_db(comment_user, footprint_id, comment)
    return True


def get_comment_list_by_footprint_id_db(footprint_id):
    """
    获取评论列表
    :param footprint_id:
    """
    return FootprintComment.objects.filter(footprint_id=footprint_id).order_by('-created_time')
