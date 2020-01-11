from footprint.models import Comment, FlowType
from user_info.manager.user_info_mananger import get_user_info_by_user_id_db


def create_comment_db(comment_user, footprint_id, comment):

    user_info = get_user_info_by_user_id_db(comment_user.id)

    return Comment.objects.create(flow_id=footprint_id, flow_type=FlowType.FOOTPRINT, user_id=comment_user.id,
                                  avatar=user_info.avatar, name=user_info.nickname,
                                  comment=comment)
