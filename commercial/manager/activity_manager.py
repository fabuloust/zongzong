from commercial.models import CommercialActivity, Club, ActivityParticipant


def get_commercial_activity_by_id_db(activity_id):
    try:
        return CommercialActivity.objects.get(id=activity_id)
    except CommercialActivity.DoesNotExist:
        return None


def get_commercial_activities_by_ids_db(ids):
    return CommercialActivity.objects.filter(id__in=ids)


def get_club_by_id_db(club_id):
    try:
        return Club.objects.get(id=club_id)
    except Club.DoesNotExist:
        return None


def create_activity_participate_record_db(activity_id, user_info_id):
    return ActivityParticipant.objects.get_or_create(activity_id=activity_id, user_info_id=user_info_id)


def build_club_info(club):
    return {
        'avatar': club.avatar,
        'name': club.name,
        'address': club.address,
        'telephone': club.telephone,
        'club_id': club.id,
    }


def build_activity_info(activity, avatar):
    return {
        'activity_id': activity.id,
        'avatar': avatar,
        'title': activity.title,
        'post_time': activity.time_detail,
        'image_list': activity.image_list,
        'distance': 1,
    }


def get_club_activities_info(club_id, start_num, end_num):
    activities = CommercialActivity.objects.filter(club_id=club_id).order_by('-created_time')[start_num: end_num]
    if not activities:
        return {}
    avatar = activities[0].avatar
    return [build_activity_info(activity, avatar) for activity in activities]


def get_activity_participants(activity_id):
    return ActivityParticipant.objects.filter(activity_id=activity_id)


def build_activity_detail(activity):
    """
    构建活动详情页信息
            top_image,
        title,
        club_name,
        avatar,
        telephone,
        introduction,
        image_list,
        detail,
        address,
        time_detail,
        description,
        total_quota,
        participants: [{user_id, avatar}]
    """
    club = activity.club
    result = {
        'top_image': activity.top_image,
        'title': activity.name,
        'club_name': club.name,
        'avatar': club.avatar,
        'telephone': club.telephone,
        'introduction': activity.introduction,
        'detail': activity.detail,
        'address': activity.address,
        'time_detail': activity.time_detail,
        'description': activity.description,
        'total_quota': activity.total_quota,
    }
    participants = get_activity_participants(activity.id)
    result.update({'participants': [{'user_id': item.user_info.user_id, 'avatar': item.user_info.avatar}
                                    for item in participants]})
    return result


def participate_activity(activity_id, user_info_id):
    activity = get_commercial_activity_by_id_db(activity_id)
    if activity.participant_num >= activity.total_quota:
        return '人数已满'
    record, created = create_activity_participate_record_db(activity_id, user_info_id)
    if not created:
        return u'请勿重复报名'
    activity.participant_num += 1
    activity.save()
    return ''
