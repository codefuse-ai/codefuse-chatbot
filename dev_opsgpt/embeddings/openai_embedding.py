# encoding: utf-8
'''
@author: 温进
@file: openai_embedding.py
@time: 2023/11/22 上午10:45
@desc:
'''
import openai
import base64
import json
import os
from loguru import logger


class OpenAIEmbedding:
    def __init__(self):
        pass

    def get_emb(self, text_list):
        openai.api_key = os.environ["OPENAI_API_KEY"]
        openai.api_base = os.environ["API_BASE_URL"]

        # change , to ，to avoid bug
        modified_text_list = [i.replace(',', '，') for i in text_list]

        emb_all_result = openai.Embedding.create(
            model="text-embedding-ada-002",
            input=modified_text_list
        )

        res = {}
        # logger.debug(emb_all_result)
        logger.debug(f'len of result={len(emb_all_result["data"])}')
        for emb_result in emb_all_result['data']:
            index = emb_result['index']
            # logger.debug(index)
            text = text_list[index]
            emb = emb_result['embedding']
            res[text] = emb

        return res


if __name__ == '__main__':
    oae = OpenAIEmbedding()
    res = oae.get_emb(text_list=['这段代码是一个OkHttp拦截器，用于在请求头中添加授权令牌。它继承自`com.theokanning.openai.client.AuthenticationInterceptor`类，并且被标记为`@Deprecated`，意味着它已经过时了。\n\n这个拦截器的作用是在每个请求的头部添加一个名为"Authorization"的字段，值为传入的授权令牌。这样，当请求被发送到服务器时，服务器可以使用这个令牌来验证请求的合法性。\n\n这段代码的构造函数接受一个令牌作为参数，并将其传递给父类的构造函数。这个令牌应该是一个有效的授权令牌，用于访问受保护的资源。', '这段代码定义了一个接口`OpenAiApi`，并使用`@Deprecated`注解将其标记为已过时。它还扩展了`com.theokanning.openai.client.OpenAiApi`接口。\n\n`@Deprecated`注解表示该接口已经过时，不推荐使用。开发者应该使用`com.theokanning.openai.client.OpenAiApi`接口代替。\n\n注释中提到这个接口只是为了保持向后兼容性。这意味着它可能是为了与旧版本的代码兼容而保留的，但不推荐在新代码中使用。', '这段代码是一个OkHttp的拦截器，用于在请求头中添加授权令牌（authorization token）。\n\n在这个拦截器中，首先获取到传入的授权令牌（token），然后在每个请求的构建过程中，使用`newBuilder()`方法创建一个新的请求构建器，并在该构建器中添加一个名为"Authorization"的请求头，值为"Bearer " + token。最后，使用该构建器构建一个新的请求，并通过`chain.proceed(request)`方法继续处理该请求。\n\n这样，当使用OkHttp发送请求时，该拦截器会自动在请求头中添加授权令牌，以实现身份验证的功能。', '这段代码是一个Java接口，用于定义与OpenAI API进行通信的方法。它包含了各种不同类型的请求和响应方法，用于与OpenAI API的不同端点进行交互。\n\n接口中的方法包括：\n- `listModels()`：获取可用的模型列表。\n- `getModel(String modelId)`：获取指定模型的详细信息。\n- `createCompletion(CompletionRequest request)`：创建文本生成的请求。\n- `createChatCompletion(ChatCompletionRequest request)`：创建聊天式文本生成的请求。\n- `createEdit(EditRequest request)`：创建文本编辑的请求。\n- `createEmbeddings(EmbeddingRequest request)`：创建文本嵌入的请求。\n- `listFiles()`：获取已上传文件的列表。\n- `uploadFile(RequestBody purpose, MultipartBody.Part file)`：上传文件。\n- `deleteFile(String fileId)`：删除文件。\n- `retrieveFile(String fileId)`：获取文件的详细信息。\n- `retrieveFileContent(String fileId)`：获取文件的内容。\n- `createFineTuningJob(FineTuningJobRequest request)`：创建Fine-Tuning任务。\n- `listFineTuningJobs()`：获取Fine-Tuning任务的列表。\n- `retrieveFineTuningJob(String fineTuningJobId)`：获取指定Fine-Tuning任务的详细信息。\n- `cancelFineTuningJob(String fineTuningJobId)`：取消Fine-Tuning任务。\n- `listFineTuningJobEvents(String fineTuningJobId)`：获取Fine-Tuning任务的事件列表。\n- `createFineTuneCompletion(CompletionRequest request)`：创建Fine-Tuning模型的文本生成请求。\n- `createImage(CreateImageRequest request)`：创建图像生成的请求。\n- `createImageEdit(RequestBody requestBody)`：创建图像编辑的请求。\n- `createImageVariation(RequestBody requestBody)`：创建图像变体的请求。\n- `createTranscription(RequestBody requestBody)`：创建音频转录的请求。\n- `createTranslation(RequestBody requestBody)`：创建音频翻译的请求。\n- `createModeration(ModerationRequest request)`：创建内容审核的请求。\n- `getEngines()`：获取可用的引擎列表。\n- `getEngine(String engineId)`：获取指定引擎的详细信息。\n- `subscription()`：获取账户订阅信息。\n- `billingUsage(LocalDate starDate, LocalDate endDate)`：获取账户消费信息。\n\n这些方法使用不同的HTTP请求类型（GET、POST、DELETE）和路径来与OpenAI API进行交互，并返回相应的响应数据。'])
    # res = oae.get_emb(text_list=['''test1"test2test3''', '''test4test5test6'''])
    print(res)
