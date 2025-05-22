import os
import time
import json
import web
from urllib.parse import urlparse
import requests
import mimetypes
import cv2
from PIL import Image
import numpy as np
import imghdr
import hashlib
import re
from bridge.context import Context, ContextType
from bridge.reply import Reply, ReplyType
from channel.chat_channel import ChatChannel
from channel.gewechat.gewechat_message import GeWeChatMessage
from common.log import logger
from common.singleton import singleton
from common.tmp_dir import TmpDir
from config import conf, save_config
from lib.gewechat import GewechatClient
from voice.audio_convert import mp3_to_silk, split_audio
import uuid
import threading
import glob

MAX_UTF8_LEN = 2048

@singleton
class GeWeChatChannel(ChatChannel):
    NOT_SUPPORT_REPLYTYPE = []

    def __init__(self):
        super().__init__()

        self.callback_port = 9919  # 默认端口
        self.app_id = None  # 初始化 app_id 为 None
        self.token = None  # 初始化 token 为 None
        
        # 设置临时文件的最大保留时间（3小时）
        self.temp_file_max_age = 3 * 60 * 60  # 秒
        
        # 启动定期清理任务
        self._start_cleanup_task()

        self.base_url = conf().get("gewechat_base_url")
        if not self.base_url:
            logger.error("[gewechat] base_url is not set")
            return

        # 创建一个没有 token 的客户端用于获取 token
        self.client = GewechatClient(self.base_url, None)
        
        # 获取 token
        try:
            token_resp = self.client.get_token()
            if token_resp.get("ret") != 200:
                logger.error(f"[gewechat] get token failed: {token_resp}")
                return
            self.token = token_resp.get("data")
            conf().set("gewechat_token", self.token)
            save_config()
            logger.info(f"[gewechat] new token saved: {self.token}")
        except Exception as e:
            logger.error(f"[gewechat] Failed to get token: {str(e)}")
            return

        # 使用获取到的 token 创建新的客户端
        self.client = GewechatClient(self.base_url, self.token)

        # 获取已保存的 app_id
        self.app_id = conf().get("gewechat_app_id")
        if not self.app_id:
            logger.warning("[gewechat] app_id is not set，trying to get new app_id when login")

        self.download_url = conf().get("gewechat_download_url")
        if not self.download_url:
            logger.warning("[gewechat] download_url is not set, unable to download image")

        logger.info(f"[gewechat] init: base_url: {self.base_url}, token: {self.token}, app_id: {self.app_id}, download_url: {self.download_url}")

    def _start_cleanup_task(self):
        """启动定期清理任务"""
        def _do_cleanup():
            while True:
                try:
                    # 清理音频文件
                    self._cleanup_audio_files()
                    # 清理视频文件
                    self._cleanup_video_files()
                    # 清理图片文件
                    self._cleanup_image_files()
                    # 每30分钟执行一次清理
                    time.sleep(30 * 60)
                except Exception as e:
                    logger.error(f"[gewechat] 清理任务异常: {e}")
                    time.sleep(60)  # 发生错误时等待1分钟后重试

        cleanup_thread = threading.Thread(target=_do_cleanup, daemon=True)
        cleanup_thread.start()
        logger.info("[gewechat] 清理任务已启动")

    def _cleanup_audio_files(self):
        """清理过期的音频文件"""
        try:
            # 获取临时目录
            tmp_dir = TmpDir().path()
            current_time = time.time()
            # 音频文件最大保留3小时
            max_age = 3 * 60 * 60  

            # 清理.mp3和.silk文件
            for ext in ['.mp3', '.silk']:
                pattern = os.path.join(tmp_dir, f'*{ext}')
                for fpath in glob.glob(pattern):
                    try:
                        # 获取文件修改时间
                        mtime = os.path.getmtime(fpath)
                        # 如果文件超过最大保留时间，则删除
                        if current_time - mtime > max_age:
                            os.remove(fpath)
                            logger.debug(f"[gewechat] 清理过期音频文件: {fpath}")
                    except Exception as e:
                        logger.warning(f"[gewechat] 清理音频文件失败 {fpath}: {e}")

        except Exception as e:
            logger.error(f"[gewechat] 音频文件清理任务异常: {e}")

    def _cleanup_video_files(self):
        """清理过期的视频文件"""
        try:
            # 获取临时目录
            tmp_dir = TmpDir().path()
            current_time = time.time()
            # 视频文件最大保留2天
            max_age = 2 * 24 * 60 * 60  

            # 清理.mp4文件
            pattern = os.path.join(tmp_dir, '*.mp4')
            for fpath in glob.glob(pattern):
                try:
                    # 获取文件修改时间
                    mtime = os.path.getmtime(fpath)
                    # 如果文件超过最大保留时间，则删除
                    if current_time - mtime > max_age:
                        os.remove(fpath)
                        logger.debug(f"[gewechat] 清理过期视频文件: {fpath}")
                except Exception as e:
                    logger.warning(f"[gewechat] 清理视频文件失败 {fpath}: {e}")

        except Exception as e:
            logger.error(f"[gewechat] 视频文件清理任务异常: {e}")

    def _cleanup_image_files(self):
        """清理过期的图片文件"""
        try:
            # 获取临时目录
            tmp_dir = TmpDir().path()
            current_time = time.time()
            # 图片文件最大保留3天
            max_age = 3 * 24 * 60 * 60  

            # 清理.png和.jpg文件
            for ext in ['*.png', '*.jpg']:
                pattern = os.path.join(tmp_dir, ext)
                for fpath in glob.glob(pattern):
                    try:
                        # 获取文件修改时间
                        mtime = os.path.getmtime(fpath)
                        # 如果文件超过最大保留时间，则删除
                        if current_time - mtime > max_age:
                            file_size = os.path.getsize(fpath) / 1024  # 转换为KB
                            os.remove(fpath)
                            logger.debug(f"[gewechat] 清理过期图片文件: {fpath} (大小: {file_size:.1f}KB)")
                    except Exception as e:
                        logger.warning(f"[gewechat] 清理图片文件失败 {fpath}: {e}")

        except Exception as e:
            logger.error(f"[gewechat] 图片文件清理任务异常: {e}")

    def startup(self):
        try:
            # 如果app_id为空或登录后获取到新的app_id，保存配置
            app_id, error_msg = self.client.login(self.app_id)
            if error_msg:
                logger.error(f"[gewechat] login failed: {error_msg}")
                return

            # 如果原来的self.app_id为空或登录后获取到新的app_id，保存配置
            if not self.app_id or self.app_id != app_id:
                conf().set("gewechat_app_id", app_id)
                save_config()
                logger.info(f"[gewechat] new app_id saved: {app_id}")
                self.app_id = app_id

            # 获取回调地址
            callback_url = conf().get("gewechat_callback_url")
            if not callback_url:
                logger.error("[gewechat] callback_url is not set, unable to start callback server")
                return
            
            parsed_url = urlparse(callback_url)
            path = parsed_url.path
            self.callback_port = parsed_url.port or 9919
            
            # 创建新线程设置回调地址
            import threading
            def set_callback():
                import time
                logger.info("[gewechat] sleep 3 seconds waiting for server to start, then set callback")
                time.sleep(3)

                try:
                    callback_resp = self.client.set_callback(self.token, callback_url)
                    logger.info(f"[gewechat] Callback response: {callback_resp}")
                    
                    if callback_resp.get("ret") not in [200, 0]:
                        logger.warning(f"[gewechat] set callback warning: {callback_resp}")
                    else:
                        logger.info("[gewechat] callback set successfully")
                        
                except Exception as e:
                    logger.error(f"[gewechat] Exception when setting callback: {str(e)}")
                    raise

            callback_thread = threading.Thread(target=set_callback, daemon=True)
            callback_thread.start()

            # 启动回调服务器
            urls = (path, "channel.gewechat.gewechat_channel.Query")
            app = web.application(urls, globals(), autoreload=False)
            logger.info(f"[gewechat] Starting callback server on port {self.callback_port}")
            web.httpserver.runsimple(app.wsgifunc(), ("0.0.0.0", self.callback_port))
        except Exception as e:
            logger.error(f"[gewechat] Error in startup: {str(e)}")
            raise

    def get_segment_durations(self, file_paths):
        """
        获取每段音频的时长
        :param file_paths: 分段文件路径列表
        :return: 每段时长列表（毫秒）
        """
        from pydub import AudioSegment
        durations = []
        for path in file_paths:
            audio = AudioSegment.from_file(path)
            durations.append(len(audio))
        return durations

    def _extract_markdown_images(self, text):
        """
        从markdown文本中提取图片链接和普通链接
        返回: (处理后的文本, 图片URL列表)
        """
        # 同时匹配图片语法和链接语法
        patterns = [
            r'!\[.*?\]\((.*?)\)',  # markdown图片语法 ![图片](url)
            r'!\[image\]\((.*?)\)',  # API返回的图片语法 ![image](url)
            r'\[图片.*?链接\]\((.*?)\)',  # 图片链接语法 [图片链接](url)
            r'\[图片\]\((.*?)\)',  # 简单链接语法 [图片](url)
            r'\[点击查看\]\((.*?)\)',  # 点击查看链接语法 [点击查看](url)
            r'\[.*?\]\((https?://[^\s)]+)\)'  # 通用链接语法 [任意文本](url)
        ]
        
        # 存储图片URL
        image_urls = []
        processed_text = text
        
        logger.debug(f"[gewechat] Processing text for images: {text}")
        
        def is_image_url(url):
            """判断是否为图片URL"""
            # coze平台特殊图片链接格式
            if 'coze.cn/t/' in url and not url.endswith(('.html', '.htm')):
                return True
            # 常规图片格式
            if url.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                return True
            return False
        
        # 处理所有匹配模式
        for pattern in patterns:
            # 查找所有匹配
            matches = list(re.finditer(pattern, processed_text))
            logger.debug(f"[gewechat] Found {len(matches)} matches with pattern: {pattern}")
            
            # 从后向前处理，避免影响前面的索引位置
            for match in reversed(matches):
                # 添加图片URL到列表
                url = match.group(1)
                # 检查URL是否是图片链接
                if is_image_url(url):
                    image_urls.append(url)
                    logger.debug(f"[gewechat] Extracted image URL: {url}")
                    # 替换markdown格式为纯URL
                    processed_text = (
                        processed_text[:match.start()].strip() + 
                        f" {url} " +  # 保留URL在文本中
                        processed_text[match.end():].strip()
                    )
                else:
                    logger.debug(f"[gewechat] Skipped non-image URL: {url}")
        
        logger.debug(f"[gewechat] Processed text: {processed_text}")
        logger.debug(f"[gewechat] Extracted URLs: {image_urls}")
        
        return processed_text.strip(), image_urls

    def send(self, reply: Reply, context: Context):
        receiver = context["receiver"]
        gewechat_message = context.get("msg")
        
        if reply.type in [ReplyType.TEXT, ReplyType.ERROR, ReplyType.INFO]:
            reply_text = reply.content
            ats = ""
            if gewechat_message and gewechat_message.is_group:
                ats = gewechat_message.actual_user_id
            
            # 处理markdown图片
            processed_text, image_urls = self._extract_markdown_images(reply_text)
            logger.debug(f"[gewechat] After processing markdown - Text: {processed_text}, Images: {image_urls}")
            
            # 处理引用消息
            if context.get("is_reference") and context.get("reference_id"):
                try:
                    # 构建引用消息的XML
                    ref_type = "1" if reply.type in [ReplyType.TEXT, ReplyType.ERROR, ReplyType.INFO] else "3"
                    ref_xml = f'''<?xml version="1.0"?>
                    <msg>
                        <appmsg appid="" sdkver="0">
                            <title>{processed_text}</title>
                            <des />
                            <action />
                            <type>57</type>
                            <showtype>0</showtype>
                            <soundtype>0</soundtype>
                            <mediatagname />
                            <messageext />
                            <messageaction />
                            <content />
                            <contentattr>0</contentattr>
                            <url />
                            <lowurl />
                            <dataurl />
                            <lowdataurl />
                            <appattach>
                                <totallen>0</totallen>
                                <attachid />
                                <emoticonmd5 />
                                <fileext />
                                <aeskey />
                            </appattach>
                            <extinfo />
                            <sourceusername />
                            <sourcedisplayname />
                            <thumburl />
                            <md5 />
                            <statextstr />
                            <refermsg>
                                <type>{ref_type}</type>
                                <svrid>{context["reference_id"]}</svrid>
                                <fromusr>{context["from_user_id"]}</fromusr>
                                <chatusr>{context["from_user_id"]}</chatusr>
                                <displayname>{context.get("from_user_nickname", "")}</displayname>
                                <content>{processed_text}</content>
                            </refermsg>
                        </appmsg>
                        <fromusername>{context["from_user_id"]}</fromusername>
                        <scene>0</scene>
                        <appinfo>
                            <version>1</version>
                            <appname></appname>
                        </appinfo>
                        <commenturl></commenturl>
                    </msg>'''
                    
                    # 使用 post_app_msg 发送引用消息
                    result = self.client.post_app_msg(self.app_id, receiver, ref_xml)
                    if result.get("ret") == 200:
                        logger.info(f"[gewechat] Reference message sent successfully")
                        return
                    else:
                        logger.warning(f"[gewechat] Failed to send reference message: {result}")
                        # 如果发送失败，继续使用普通文本发送
                except Exception as e:
                    logger.error(f"[gewechat] Error sending reference message: {str(e)}")
                    # 如果发送失败，继续使用普通文本发送
            
            # 保持原有的文本分段发送逻辑
            messages = processed_text.split("//n")
            messages = [msg.strip() for msg in messages if msg.strip()]
            
            # 分段发送文本
            for i, msg in enumerate(messages):
                try:
                    # 只在第一段添加@信息
                    if i == 0:
                        self.client.post_text(self.app_id, receiver, msg, ats)
                    else:
                        self.client.post_text(self.app_id, receiver, msg, "")
                        
                    logger.info(f"[gewechat] Send message part {i+1}/{len(messages)}: {msg}")
                    
                    # 添加发送间隔，避免消息发送太快
                    if i < len(messages) - 1:
                        time.sleep(0.5)
                        
                except Exception as e:
                    logger.error(f"[gewechat] Failed to send message: {str(e)}")
                    continue
            
            # 发送提取出的图片
            for img_url in image_urls:
                try:
                    time.sleep(0.5)  # 添加延迟避免消息发送太快
                    logger.debug(f"[gewechat] Attempting to send image: {img_url}")
                    self.client.post_image(self.app_id, receiver, img_url)
                    logger.info(f"[gewechat] Successfully sent markdown image: {img_url}")
                except Exception as e:
                    logger.error(f"[gewechat] Failed to send markdown image: {str(e)}")
                    continue
                            
        elif reply.type == ReplyType.VOICE:
            try:
                content = reply.content
                if not content or not os.path.exists(content):
                    logger.error(f"[gewechat] 语音文件未找到: {content}")
                    return

                if not content.endswith('.mp3'):
                    logger.error(f"[gewechat] 仅支持MP3格式: {content}")
                    return

                # 创建临时文件列表用于后续清理
                temp_files = []
                
                try:
                    # 分割音频文件
                    audio_length_ms, files = split_audio(content, 60 * 1000)
                    if not files:
                        logger.error("[gewechat] 音频分割失败")
                        return
                        
                    temp_files.extend(files)  # 添加分割后的文件到清理列表
                    logger.info(f"[gewechat] 音频分割完成，共 {len(files)} 段")
                    
                    # 获取每段时长
                    segment_durations = self.get_segment_durations(files)
                    tmp_dir = TmpDir().path()
                    
                    # 预先转换所有文件
                    silk_files = []
                    callback_url = conf().get("gewechat_callback_url")
                    
                    for i, fcontent in enumerate(files, 1):
                        try:
                            # 转换为SILK格式
                            silk_name = f"{os.path.basename(fcontent)}_{i}.silk"
                            silk_path = os.path.join(tmp_dir, silk_name)
                            temp_files.append(silk_path)
                            
                            duration = mp3_to_silk(fcontent, silk_path)
                            if duration > 0 and os.path.exists(silk_path):
                                silk_url = callback_url + "?file=" + silk_path
                                silk_files.append((silk_url, duration))
                                logger.info(f"[gewechat] 第 {i} 段转换成功，时长: {duration/1000:.1f}秒")
                            else:
                                raise Exception(f"转换失败: {fcontent}")
                                
                        except Exception as e:
                            logger.error(f"[gewechat] 第 {i} 段转换失败: {e}")
                            return
                    
                    # 发送所有语音片段
                    for i, (silk_url, duration) in enumerate(silk_files, 1):
                        try:
                            self.client.post_voice(self.app_id, receiver, silk_url, duration)
                            logger.info(f"[gewechat] 发送第 {i}/{len(silk_files)} 段语音")
                            
                            # 固定0.3秒的发送间隔
                            if i < len(silk_files):
                                time.sleep(0.3)
                                
                        except Exception as e:
                            logger.error(f"[gewechat] 发送第 {i} 段语音失败: {e}")
                            continue
                    
                finally:
                    # 清理所有临时文件
                    for temp_file in temp_files:
                        try:
                            if os.path.exists(temp_file):
                                os.remove(temp_file)
                                logger.debug(f"[gewechat] 清理临时文件: {temp_file}")
                        except Exception as e:
                            logger.warning(f"[gewechat] 清理文件失败 {temp_file}: {e}")
                            
            except Exception as e:
                logger.error(f"[gewechat] 语音处理失败: {e}")
                
        elif reply.type == ReplyType.APP:
            try:
                logger.info("[gewechat] APP message raw content type: {}, content: {}".format(type(reply.content), reply.content))
                
                # 直接使用 XML 内容
                if not isinstance(reply.content, str):
                    logger.error(f"[gewechat] send app message failed: content must be XML string, got type={type(reply.content)}")
                    return
                
                if not reply.content.strip():
                    logger.error("[gewechat] send app message failed: content is empty string")
                    return
                
                # 直接发送 appmsg 内容
                result = self.client.post_app_msg(self.app_id, receiver, reply.content)
                logger.info("[gewechat] sendApp, receiver={}, content={}, result={}".format(
                    receiver, reply.content, result))
                return result
                
            except Exception as e:
                logger.error(f"[gewechat] send app message failed: {str(e)}")
                return

        elif reply.type == ReplyType.IMAGE_URL:
            img_url = reply.content
            self.client.post_image(self.app_id, receiver, img_url)
            logger.info("[gewechat] sendImage url={}, receiver={}".format(img_url, receiver))
            
        elif reply.type == ReplyType.IMAGE:
            image_storage = reply.content
            image_storage.seek(0)
            # Save image to tmp directory
            img_data = image_storage.read()

            # 检查是否为GIF格式
            img_type = imghdr.what(None, h=img_data)

            # 根据图片类型设置正确的扩展名
            extension = ".gif" if img_type == "gif" else ".png"
            img_file_name = f"img_{str(uuid.uuid4())}{extension}"
            img_file_path = TmpDir().path() + img_file_name

            with open(img_file_path, "wb") as f:
                f.write(img_data)

            # 构造回调 URL
            callback_url = conf().get("gewechat_callback_url")
            img_url = callback_url + "?file=" + img_file_path

            # 如果是GIF，使用post_emoji而不是post_image
            if img_type == "gif":
                # 获取文件大小
                emoji_size = os.path.getsize(img_file_path)
                # 计算文件的MD5
                emoji_md5 = hashlib.md5(img_data).hexdigest()

                self.client.post_emoji(self.app_id, receiver, emoji_md5=emoji_md5, emoji_size=emoji_size)
                logger.info("[gewechat] sendEmoji, receiver={}, md5={}, size={}".format(
                    receiver, emoji_md5, emoji_size))
            else:
                # 生成缩略图时保持原图尺寸
                image = Image.open(img_file_path)
                thumb_file_name = f"thumb_{str(uuid.uuid4())}{extension}"
                thumb_file_path = TmpDir().path() + thumb_file_name
                image.save(thumb_file_path)

                # 构造本地 URL
                callback_url = conf().get("gewechat_callback_url")
                local_thumb_url = callback_url + "?file=" + thumb_file_path

                self.client.post_image(self.app_id, receiver, local_thumb_url)
                logger.info("[gewechat] sendImage, receiver={}, url={}".format(receiver, local_thumb_url))

        elif reply.type == ReplyType.VIDEO_URL:
            try:
                video_url = reply.content
                # 使用视频URL作为缩略图
                thumb_url = video_url
                # 默认视频时长设为10秒
                video_duration = 10
                result = self.send_video(receiver, video_url, thumb_url, video_duration)
                if result:
                    logger.info(f"[gewechat] Video sent successfully to {receiver}: {video_url}")
                else:
                    logger.error(f"[gewechat] Failed to send video to {receiver}: {video_url}")
            except Exception as e:
                logger.error(f"[gewechat] send video failed: {e}")

    def send_video(self, to_wxid, video_url, thumb_url, video_duration):
        """发送视频消息
        Args:
            to_wxid: 接收人wxid
            video_url: 视频URL
            thumb_url: 视频缩略图URL
            video_duration: 视频时长(秒)
        Returns:
            dict: 发送结果
        """
        try:
            # 下载视频到本地临时目录
            video_file_name = f"video_{str(uuid.uuid4())}.mp4"
            video_file_path = TmpDir().path() + video_file_name

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            # 下载视频
            with requests.get(video_url, headers=headers, stream=True) as r:
                r.raise_for_status()
                with open(video_file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

            # 生成缩略图
            thumb_file_name = f"thumb_{str(uuid.uuid4())}.jpg"
            thumb_file_path = TmpDir().path() + thumb_file_name

            # 使用OpenCV读取视频第一帧作为缩略图
            cap = cv2.VideoCapture(video_file_path)
            ret, frame = cap.read()
            if ret:
                # 获取视频时长
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                video_duration = int(frame_count / fps) if fps > 0 else 10

                # 保持原图尺寸
                image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                image.save(thumb_file_path, 'JPEG', quality=95)
            else:
                # 如果无法读取视频帧，创建一个默认的黑色缩略图
                image = Image.new('RGB', (480, 270), color='black')
                image.save(thumb_file_path, 'JPEG', quality=95)

            cap.release()

            # 构造本地 URL
            callback_url = conf().get("gewechat_callback_url")
            local_thumb_url = callback_url + "?file=" + thumb_file_path

            # 发送视频
            resp = self.client.post_video(
                self.app_id,
                to_wxid,
                video_url,
                local_thumb_url,  # 使用生成的缩略图
                video_duration
            )

            if resp.get("ret")!= 200:
                logger.error(f"[gewechat] send video failed: {resp}")
                return None

            return resp.get("data")

        except Exception as e:
            logger.error(f"[gewechat] send video error: {e}")
            return None


class Query:
    def GET(self):
        # 搭建简单的文件服务器，用于向gewechat服务传输语音等文件，但只允许访问tmp目录下的文件
        params = web.input(file="")
        file_path = params.file
        if file_path:
            # 使用os.path.abspath清理路径
            clean_path = os.path.abspath(file_path)
            # 获取tmp目录的绝对路径
            tmp_dir = os.path.abspath("tmp")
            # 检查文件路径是否在tmp目录下
            if not clean_path.startswith(tmp_dir):
                logger.error(f"[gewechat] Forbidden access to file outside tmp directory: file_path={file_path}, clean_path={clean_path}, tmp_dir={tmp_dir}")
                raise web.forbidden()

            if os.path.exists(clean_path):
                # 获取文件类型
                file_type = mimetypes.guess_type(clean_path)[0]

                # 设置正确的Content-Type
                web.header('Content-Type', file_type or 'application/octet-stream')

                # 如果是视频文件，添加必要的响应头
                if file_type and file_type.startswith('video/'):
                    web.header('Accept-Ranges', 'bytes')

                with open(clean_path, 'rb') as f:
                    return f.read()
            else:
                logger.error(f"[gewechat] File not found: {clean_path}")
                raise web.notfound()
        return "gewechat callback server is running"

    def POST(self):
        channel = GeWeChatChannel()
        data = json.loads(web.data())
        logger.debug("[gewechat] receive data: {}".format(data))
        
        # gewechat服务发送的回调测试消息
        if isinstance(data, dict) and 'testMsg' in data and 'token' in data:
            logger.debug(f"[gewechat] 收到gewechat服务发送的回调测试消息")
            return "success"

        gewechat_msg = GeWeChatMessage(data, channel.client)
        
        # 微信客户端的状态同步消息
        if gewechat_msg.ctype == ContextType.STATUS_SYNC:
            logger.debug(f"[gewechat] ignore status sync message: {gewechat_msg.content}")
            return "success"

        # 忽略非用户消息（如公众号、系统通知等）
        if gewechat_msg.ctype == ContextType.NON_USER_MSG:
            logger.debug(f"[gewechat] ignore non-user message from {gewechat_msg.from_user_id}: {gewechat_msg.content}")
            return "success"

        # 判断是否需要忽略语音消息
        if gewechat_msg.ctype == ContextType.VOICE:
            if conf().get("speech_recognition") != True:
                return "success"

        # 忽略来自自己的消息
        if gewechat_msg.my_msg:
            logger.debug(f"[gewechat] ignore message from myself: {gewechat_msg.actual_user_id}: {gewechat_msg.content}")
            return "success"

        # 忽略过期的消息
        if int(gewechat_msg.create_time) < int(time.time()) - 60 * 5: # 跳过5分钟前的历史消息
            logger.debug(f"[gewechat] ignore expired message from {gewechat_msg.actual_user_id}: {gewechat_msg.content}")
            return "success"

        context = channel._compose_context(
            gewechat_msg.ctype,
            gewechat_msg.content,
            isgroup=gewechat_msg.is_group,
            msg=gewechat_msg,
        )
        if context:
            channel.produce(context)
        return "success"