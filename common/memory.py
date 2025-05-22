from common.expired_dict import ExpiredDict

USER_IMAGE_CACHE = ExpiredDict(60 * 3)
USER_VIDEO_CACHE = ExpiredDict(60 * 3)  # 添加视频缓存，过期时间为3分钟