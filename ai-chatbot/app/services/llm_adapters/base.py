from abc import ABC, abstractmethod


class BaseLlmAdapter(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def stream(self, system_prompt: str, user_prompt: str):
        raise NotImplementedError