from bot.session_manager import Session

class DeepSeekSession(Session):
    def __init__(self, session_id, system_prompt=None, model=None):
        super().__init__(session_id, system_prompt)
        self.model = model
        self.reset()  # 初始化时调用reset来设置系统提示词

    def build_messages(self):
        """
        构造messages，供发送给DeepSeek接口
        :return: messages
        """
        messages = []
        if self.system_prompt:
            messages.append({
                "role": "system",
                "content": self.system_prompt
            })
        for item in self.messages:
            messages.append({
                "role": item["role"],
                "content": item["content"]
            })
        return messages
