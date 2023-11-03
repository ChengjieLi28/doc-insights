from llama_index import PromptTemplate
from llama_index.indices.service_context import ServiceContext
from llama_index.prompts.prompt_type import PromptType
from llama_index.prompts.prompts import QuestionAnswerPrompt, RefinePrompt
from llama_index.response_synthesizers import BaseSynthesizer
from llama_index.response_synthesizers.factory import get_response_synthesizer

from .utils import build_title_for_document


def get_custom_response_synthesizer(
    service_context: ServiceContext, documents
) -> BaseSynthesizer:
    doc_titles = "\n".join("- " + build_title_for_document(doc) for doc in documents)

    refine_template_str = f"""
用户选择了一组基金文档，并询问了有关这些文件的问题。这些基金文件的标题如下:
{doc_titles}
原始查询如下:{{query_str}}
我们已经提供了一个答案:{{existing_answer}}
如果需要请改善现有的答案 ，以下有更多的背景信息。
------------
{{context_msg}}
------------
考虑到新的上下文，将原来的答案改进为更好的答案回答这个问题。如果上下文没有用，则返回原始答案。
完善后的回答:
""".strip()
    refine_prompt = RefinePrompt(
        template=refine_template_str, prompt_type=PromptType.REFINE
    )

    qa_template_str = f"""
用户选择了一组基金文档，并询问了有关这些文件的问题。基金文件的标题如下:
{doc_titles}
下面是上下文信息。
---------------------
{{context_str}}
---------------------
给定上下文信息而不是先验知识，回答这个问题，总是使用中文回复。
问题: {{query_str}}
回答:
""".strip()
    qa_prompt = QuestionAnswerPrompt(
        template=qa_template_str,
        prompt_type=PromptType.QUESTION_ANSWER,
    )

    return get_response_synthesizer(
        service_context, refine_template=refine_prompt, text_qa_template=qa_prompt
    )


def get_template():
    return PromptTemplate(
        """
Given a conversation (between Human and Assistant) and a follow up message from Human, \
rewrite the message to be a standalone question that captures all relevant context \
from the conversation.

<Chat History>
{chat_history}

<Follow Up Message>
{question}

<Standalone question>
""".strip()
    )


def get_sys_prompt():
    return """
你是一个基金公司的客服，你总是根据用户提供的文档用最相关的信息回答问题，文档中包含有关用户感兴趣的基金产品的信息。

以下是一些你必须遵循的准则:

- 对于基金问题，你必须从用户提供的的文件找到答案，然后编写一个有用的回答。
- 即使提供的文件似乎无法回答问题，你仍然必须使用它们来找到最相关的信息和见解，不使用它们会让用户觉得你没有履行自己的职责。
- 你可以假设用户提出的问题与提供的文件有关。
- 如果你无法找到答案，你应该说你没有找到答案，仍然尽可能传递从文档中找到的有用信息。
- 当用户询问任何与基金产品无关的信息时，礼貌地拒绝回应，并建议用户提出相关问题。
- 但如果你发现用户不是在提问，而是对基金的表现进行抱怨或指责时，请进行情绪上的安抚。

记住，你只扮演客服的角色，不要模拟客户的问题。你必须总是用中文回答问题。
"""
