from typing import Dict, Any
from ..util.http_util import post_json

class MessageApi:
    def __init__(self, base_url: str, token: str):
        """初始化消息API
        
        Args:
            base_url: API基础URL
            token: 认证token
        """
        self.base_url = base_url
        self.token = token

    def post_text(self, app_id: str, to_wxid: str, content: str, ats: str) -> Dict[str, Any]:
        """发送文字消息
        
        Args:
            app_id: 应用ID
            to_wxid: 接收人wxid
            content: 消息内容
            ats: @的用户列表，多个用户用逗号分隔
            
        Returns:
            Dict[str, Any]: API响应结果
        """
        param = {
            "appId": app_id,
            "toWxid": to_wxid,
            "content": content,
            "ats": ats
        }
        return post_json(self.base_url, "/message/postText", self.token, param)

    def post_file(self, app_id: str, to_wxid: str, file_url: str, file_name: str) -> Dict[str, Any]:
        """发送文件消息
        
        Args:
            app_id: 应用ID
            to_wxid: 接收人wxid
            file_url: 文件URL
            file_name: 文件名
            
        Returns:
            Dict[str, Any]: API响应结果
        """
        param = {
            "appId": app_id,
            "toWxid": to_wxid,
            "fileUrl": file_url,
            "fileName": file_name
        }
        return post_json(self.base_url, "/message/postFile", self.token, param)

    def post_image(self, app_id: str, to_wxid: str, img_url: str) -> Dict[str, Any]:
        """发送图片消息
        
        Args:
            app_id: 应用ID
            to_wxid: 接收人wxid
            img_url: 图片URL
            
        Returns:
            Dict[str, Any]: API响应结果
        """
        param = {
            "appId": app_id,
            "toWxid": to_wxid,
            "imgUrl": img_url
        }
        return post_json(self.base_url, "/message/postImage", self.token, param)

    def post_voice(self, app_id: str, to_wxid: str, voice_url: str, voice_duration: int) -> Dict[str, Any]:
        """发送语音消息
        
        Args:
            app_id: 应用ID
            to_wxid: 接收人wxid
            voice_url: 语音URL
            voice_duration: 语音时长
            
        Returns:
            Dict[str, Any]: API响应结果
        """
        param = {
            "appId": app_id,
            "toWxid": to_wxid,
            "voiceUrl": voice_url,
            "voiceDuration": voice_duration
        }
        return post_json(self.base_url, "/message/postVoice", self.token, param)

    def post_video(self, app_id: str, to_wxid: str, video_url: str, thumb_url: str, video_duration: int) -> Dict[str, Any]:
        """发送视频消息
        
        Args:
            app_id: 应用ID
            to_wxid: 接收人wxid
            video_url: 视频URL
            thumb_url: 视频缩略图URL
            video_duration: 视频时长
            
        Returns:
            Dict[str, Any]: API响应结果
        """
        param = {
            "appId": app_id,
            "toWxid": to_wxid,
            "videoUrl": video_url,
            "thumbUrl": thumb_url,
            "videoDuration": video_duration
        }
        return post_json(self.base_url, "/message/postVideo", self.token, param)

    def post_link(self, app_id: str, to_wxid: str, title: str, desc: str, link_url: str, thumb_url: str) -> Dict[str, Any]:
        """发送链接消息
        
        Args:
            app_id: 应用ID
            to_wxid: 接收人wxid
            title: 链接标题
            desc: 链接描述
            link_url: 链接URL
            thumb_url: 链接缩略图URL
            
        Returns:
            Dict[str, Any]: API响应结果
        """
        param = {
            "appId": app_id,
            "toWxid": to_wxid,
            "title": title,
            "desc": desc,
            "linkUrl": link_url,
            "thumbUrl": thumb_url
        }
        return post_json(self.base_url, "/message/postLink", self.token, param)

    def post_name_card(self, app_id: str, to_wxid: str, nick_name: str, name_card_wxid: str) -> Dict[str, Any]:
        """发送名片消息
        
        Args:
            app_id: 应用ID
            to_wxid: 接收人wxid
            nick_name: 名片昵称
            name_card_wxid: 名片wxid
            
        Returns:
            Dict[str, Any]: API响应结果
        """
        param = {
            "appId": app_id,
            "toWxid": to_wxid,
            "nickName": nick_name,
            "nameCardWxid": name_card_wxid
        }
        return post_json(self.base_url, "/message/postNameCard", self.token, param)

    def post_emoji(self, app_id: str, to_wxid: str, emoji_md5: str, emoji_size: int) -> Dict[str, Any]:
        """发送emoji消息
        
        Args:
            app_id: 应用ID
            to_wxid: 接收人wxid
            emoji_md5: emoji的MD5值
            emoji_size: emoji的大小
            
        Returns:
            Dict[str, Any]: API响应结果
        """
        param = {
            "appId": app_id,
            "toWxid": to_wxid,
            "emojiMd5": emoji_md5,
            "emojiSize": emoji_size
        }
        return post_json(self.base_url, "/message/postEmoji", self.token, param)

    def post_app_msg(self, app_id: str, to_wxid: str, appmsg: str) -> Dict[str, Any]:
        """发送应用消息(如音乐卡片)
        
        Args:
            app_id: 应用ID
            to_wxid: 接收人wxid
            appmsg: 应用消息XML内容，对于音乐卡片需要包含title、desc、music_url等信息
            
        Returns:
            Dict[str, Any]: API响应结果，包含:
                - ret: 返回码，0表示成功
                - msg: 返回信息
                - data: 返回数据
        """
        param = {
            "appId": app_id,
            "toWxid": to_wxid,
            "appmsg": appmsg
        }
        return post_json(self.base_url, "/message/postAppMsg", self.token, param)

    def post_mini_app(self, app_id: str, to_wxid: str, mini_app_id: str, display_name: str, page_path: str, cover_img_url: str, title: str, user_name: str) -> Dict[str, Any]:
        """发送小程序消息
        
        Args:
            app_id: 应用ID
            to_wxid: 接收人wxid
            mini_app_id: 小程序ID
            display_name: 小程序显示名称
            page_path: 小程序页面路径
            cover_img_url: 小程序封面图片URL
            title: 小程序标题
            user_name: 小程序用户名
            
        Returns:
            Dict[str, Any]: API响应结果
        """
        param = {
            "appId": app_id,
            "toWxid": to_wxid,
            "miniAppId": mini_app_id,
            "displayName": display_name,
            "pagePath": page_path,
            "coverImgUrl": cover_img_url,
            "title": title,
            "userName": user_name
        }
        return post_json(self.base_url, "/message/postMiniApp", self.token, param)

    def forward_file(self, app_id: str, to_wxid: str, xml: str) -> Dict[str, Any]:
        """转发文件
        
        Args:
            app_id: 应用ID
            to_wxid: 接收人wxid
            xml: 文件XML内容
            
        Returns:
            Dict[str, Any]: API响应结果
        """
        param = {
            "appId": app_id,
            "toWxid": to_wxid,
            "xml": xml
        }
        return post_json(self.base_url, "/message/forwardFile", self.token, param)

    def forward_image(self, app_id: str, to_wxid: str, xml: str) -> Dict[str, Any]:
        """转发图片
        
        Args:
            app_id: 应用ID
            to_wxid: 接收人wxid
            xml: 图片XML内容
            
        Returns:
            Dict[str, Any]: API响应结果
        """
        param = {
            "appId": app_id,
            "toWxid": to_wxid,
            "xml": xml
        }
        return post_json(self.base_url, "/message/forwardImage", self.token, param)

    def forward_video(self, app_id: str, to_wxid: str, xml: str) -> Dict[str, Any]:
        """转发视频
        
        Args:
            app_id: 应用ID
            to_wxid: 接收人wxid
            xml: 视频XML内容
            
        Returns:
            Dict[str, Any]: API响应结果
        """
        param = {
            "appId": app_id,
            "toWxid": to_wxid,
            "xml": xml
        }
        return post_json(self.base_url, "/message/forwardVideo", self.token, param)

    def forward_url(self, app_id: str, to_wxid: str, xml: str) -> Dict[str, Any]:
        """转发链接
        
        Args:
            app_id: 应用ID
            to_wxid: 接收人wxid
            xml: 链接XML内容
            
        Returns:
            Dict[str, Any]: API响应结果
        """
        param = {
            "appId": app_id,
            "toWxid": to_wxid,
            "xml": xml
        }
        return post_json(self.base_url, "/message/forwardUrl", self.token, param)

    def forward_mini_app(self, app_id: str, to_wxid: str, xml: str, cover_img_url: str) -> Dict[str, Any]:
        """转发小程序
        
        Args:
            app_id: 应用ID
            to_wxid: 接收人wxid
            xml: 小程序XML内容
            cover_img_url: 小程序封面图片URL
            
        Returns:
            Dict[str, Any]: API响应结果
        """
        param = {
            "appId": app_id,
            "toWxid": to_wxid,
            "xml": xml,
            "coverImgUrl": cover_img_url
        }
        return post_json(self.base_url, "/message/forwardMiniApp", self.token, param)

    def revoke_msg(self, app_id: str, to_wxid: str, msg_id: str, new_msg_id: str, create_time: int) -> Dict[str, Any]:
        """撤回消息
        
        Args:
            app_id: 应用ID
            to_wxid: 接收人wxid
            msg_id: 消息ID
            new_msg_id: 新消息ID
            create_time: 消息创建时间
            
        Returns:
            Dict[str, Any]: API响应结果
        """
        param = {
            "appId": app_id,
            "toWxid": to_wxid,
            "msgId": msg_id,
            "newMsgId": new_msg_id,
            "createTime": create_time
        }
        return post_json(self.base_url, "/message/revokeMsg", self.token, param)