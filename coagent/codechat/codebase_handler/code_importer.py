# encoding: utf-8
'''
@author: 温进
@file: codebase_handler.py
@time: 2023/11/21 下午2:07
@desc:
'''
import time
from loguru import logger

# from configs.server_config import NEBULA_HOST, NEBULA_PORT, NEBULA_USER, NEBULA_PASSWORD, NEBULA_STORAGED_PORT
# from configs.server_config import CHROMA_PERSISTENT_PATH
# from configs.model_config import EMBEDDING_DEVICE, EMBEDDING_MODEL
from coagent.db_handler.graph_db_handler.nebula_handler import NebulaHandler
from coagent.db_handler.vector_db_handler.chroma_handler import ChromaHandler
from coagent.embeddings.get_embedding import get_embedding
from coagent.llm_models.llm_config import EmbedConfig


class CodeImporter:
    def __init__(self, codebase_name: str, embed_config: EmbedConfig, nh: NebulaHandler, ch: ChromaHandler):
        self.codebase_name = codebase_name
        # self.engine = engine
        self.embed_config: EmbedConfig= embed_config
        self.nh = nh
        self.ch = ch

    def import_code(self, static_analysis_res: dict, interpretation: dict, do_interpret: bool = True):
        '''
        import code to nebula and chroma
        @return:
        '''
        static_analysis_res = self.filter_out_vertex(static_analysis_res, interpretation)
        logger.info(f'static_analysis_res={static_analysis_res}')

        self.analysis_res_to_graph(static_analysis_res)
        self.interpretation_to_db(static_analysis_res, interpretation, do_interpret)

    def filter_out_vertex(self, static_analysis_res, interpretation):
        '''
        filter out nonexist vertices
        @param static_analysis_res:
        @param interpretation:
        @return:
        '''
        save_pac_name = set()
        for i, j in static_analysis_res.items():
            save_pac_name.add(j['pac_name'])

            for class_name in j['class_name_list']:
                save_pac_name.add(class_name)
                save_pac_name.update(j['func_name_dict'].get(class_name, []))

        for _, structure in static_analysis_res.items():
            new_pac_name_list = []
            for i in structure['import_pac_name_list']:
                if i in save_pac_name:
                    new_pac_name_list.append(i)

            structure['import_pac_name_list'] = new_pac_name_list
        return static_analysis_res

    def analysis_res_to_graph(self, static_analysis_res):
        '''
        transform static_analysis_res to tuple
        @param static_analysis_res:
        @return:
        '''
        vertex_value_dict = {
            'package':{
                'properties_name': [],
                'values': {}
            },
            'class': {
                'properties_name': [],
                'values': {}
            },
            'method': {
                'properties_name': [],
                'values': {}
            },
        }

        edge_value_dict = {
            'contain': {
                'properties_name': [],
                'values': {}
            },
            'depend': {
                'properties_name': [],
                'values': {}
            }
        }

        for _, structure in static_analysis_res.items():
            pac_name = structure['pac_name']
            vertex_value_dict['package']['values'][pac_name] = []

            for class_name in structure['class_name_list']:
                vertex_value_dict['class']['values'][class_name] = []

                edge_value_dict['contain']['values'][(pac_name, class_name)] = []

                for func_name in structure['func_name_dict'].get(class_name, []):
                    vertex_value_dict['method']['values'][func_name] = []

                    edge_value_dict['contain']['values'][(class_name, func_name)] = []

            for depend_pac_name in structure['import_pac_name_list']:
                vertex_value_dict['package']['values'][depend_pac_name] = []

                edge_value_dict['depend']['values'][(pac_name, depend_pac_name)] = []

        # create vertex
        for tag_name, value_dict in vertex_value_dict.items():
            res = self.nh.insert_vertex(tag_name, value_dict)
            logger.debug(res.error_msg())

        # create edge
        for tag_name, value_dict in edge_value_dict.items():
            res = self.nh.insert_edge(tag_name, value_dict)
            logger.debug(res.error_msg())

        return

    def interpretation_to_db(self, static_analysis_res, interpretation, do_interpret, ):
        '''
        vectorize interpretation and save to db
        @return:
        '''
        # if not do_interpret, fake some vector
        if do_interpret:
            logger.info('start get embedding for interpretion')
            interp_list = list(interpretation.values())
            emb = get_embedding(engine=self.embed_config.embed_engine, text_list=interp_list, model_path=self.embed_config.embed_model_path, embedding_device= self.embed_config.model_device)
            logger.info('get embedding done')
        else:
            emb = {i: [0] for i in list(interpretation.values())}

        ids = []
        embeddings = []
        documents = []
        metadatas = []

        for code_text, interp in interpretation.items():
            if code_text not in static_analysis_res:
                continue

            pac_name = static_analysis_res[code_text]['pac_name']
            if pac_name in ids:
                continue

            ids.append(pac_name)
            documents.append(interp)

            metadatas.append({
                'code_text': code_text
            })

            embeddings.append(emb[interp])

        # add documents to chroma
        res = self.ch.add_data(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
        logger.debug(res)

    def init_graph(self):
        '''
        init graph
        @return:
        '''
        res = self.nh.create_space(space_name=self.codebase_name, vid_type='FIXED_STRING(1024)')
        logger.debug(res.error_msg())
        time.sleep(5)

        self.nh.set_space_name(self.codebase_name)

        logger.info(f'space_name={self.nh.space_name}')
        # create tag
        tag_name = 'package'
        prop_dict = {}
        res = self.nh.create_tag(tag_name, prop_dict)
        logger.debug(res.error_msg())

        tag_name = 'class'
        prop_dict = {}
        res = self.nh.create_tag(tag_name, prop_dict)
        logger.debug(res.error_msg())

        tag_name = 'method'
        prop_dict = {}
        res = self.nh.create_tag(tag_name, prop_dict)
        logger.debug(res.error_msg())

        # create edge type
        edge_type_name = 'contain'
        prop_dict = {}
        res = self.nh.create_edge_type(edge_type_name, prop_dict)
        logger.debug(res.error_msg())

        # create edge type
        edge_type_name = 'depend'
        prop_dict = {}
        res = self.nh.create_edge_type(edge_type_name, prop_dict)
        logger.debug(res.error_msg())


if __name__ == '__main__':
    static_res = {'package com.theokanning.openai.client;\nimport com.theokanning.openai.DeleteResult;\nimport com.theokanning.openai.OpenAiResponse;\nimport com.theokanning.openai.audio.TranscriptionResult;\nimport com.theokanning.openai.audio.TranslationResult;\nimport com.theokanning.openai.billing.BillingUsage;\nimport com.theokanning.openai.billing.Subscription;\nimport com.theokanning.openai.completion.CompletionRequest;\nimport com.theokanning.openai.completion.CompletionResult;\nimport com.theokanning.openai.completion.chat.ChatCompletionRequest;\nimport com.theokanning.openai.completion.chat.ChatCompletionResult;\nimport com.theokanning.openai.edit.EditRequest;\nimport com.theokanning.openai.edit.EditResult;\nimport com.theokanning.openai.embedding.EmbeddingRequest;\nimport com.theokanning.openai.embedding.EmbeddingResult;\nimport com.theokanning.openai.engine.Engine;\nimport com.theokanning.openai.file.File;\nimport com.theokanning.openai.fine_tuning.FineTuningEvent;\nimport com.theokanning.openai.fine_tuning.FineTuningJob;\nimport com.theokanning.openai.fine_tuning.FineTuningJobRequest;\nimport com.theokanning.openai.finetune.FineTuneEvent;\nimport com.theokanning.openai.finetune.FineTuneRequest;\nimport com.theokanning.openai.finetune.FineTuneResult;\nimport com.theokanning.openai.image.CreateImageRequest;\nimport com.theokanning.openai.image.ImageResult;\nimport com.theokanning.openai.model.Model;\nimport com.theokanning.openai.moderation.ModerationRequest;\nimport com.theokanning.openai.moderation.ModerationResult;\nimport io.reactivex.Single;\nimport okhttp3.MultipartBody;\nimport okhttp3.RequestBody;\nimport okhttp3.ResponseBody;\nimport retrofit2.Call;\nimport retrofit2.http.*;\nimport java.time.LocalDate;\npublic interface OpenAiApi {\n    @GET("v1/models")\n    Single<OpenAiResponse<Model>> listModels();\n    @GET("/v1/models/{model_id}")\n    Single<Model> getModel(@Path("model_id") String modelId);\n    @POST("/v1/completions")\n    Single<CompletionResult> createCompletion(@Body CompletionRequest request);\n    @Streaming\n    @POST("/v1/completions")\n    Call<ResponseBody> createCompletionStream(@Body CompletionRequest request);\n    @POST("/v1/chat/completions")\n    Single<ChatCompletionResult> createChatCompletion(@Body ChatCompletionRequest request);\n    @Streaming\n    @POST("/v1/chat/completions")\n    Call<ResponseBody> createChatCompletionStream(@Body ChatCompletionRequest request);\n    @Deprecated\n    @POST("/v1/engines/{engine_id}/completions")\n    Single<CompletionResult> createCompletion(@Path("engine_id") String engineId, @Body CompletionRequest request);\n    @POST("/v1/edits")\n    Single<EditResult> createEdit(@Body EditRequest request);\n    @Deprecated\n    @POST("/v1/engines/{engine_id}/edits")\n    Single<EditResult> createEdit(@Path("engine_id") String engineId, @Body EditRequest request);\n    @POST("/v1/embeddings")\n    Single<EmbeddingResult> createEmbeddings(@Body EmbeddingRequest request);\n    @Deprecated\n    @POST("/v1/engines/{engine_id}/embeddings")\n    Single<EmbeddingResult> createEmbeddings(@Path("engine_id") String engineId, @Body EmbeddingRequest request);\n    @GET("/v1/files")\n    Single<OpenAiResponse<File>> listFiles();\n    @Multipart\n    @POST("/v1/files")\n    Single<File> uploadFile(@Part("purpose") RequestBody purpose, @Part MultipartBody.Part file);\n    @DELETE("/v1/files/{file_id}")\n    Single<DeleteResult> deleteFile(@Path("file_id") String fileId);\n    @GET("/v1/files/{file_id}")\n    Single<File> retrieveFile(@Path("file_id") String fileId);\n    @Streaming\n    @GET("/v1/files/{file_id}/content")\n    Single<ResponseBody> retrieveFileContent(@Path("file_id") String fileId);\n    @POST("/v1/fine_tuning/jobs")\n    Single<FineTuningJob> createFineTuningJob(@Body FineTuningJobRequest request);\n    @GET("/v1/fine_tuning/jobs")\n    Single<OpenAiResponse<FineTuningJob>> listFineTuningJobs();\n    @GET("/v1/fine_tuning/jobs/{fine_tuning_job_id}")\n    Single<FineTuningJob> retrieveFineTuningJob(@Path("fine_tuning_job_id") String fineTuningJobId);\n    @POST("/v1/fine_tuning/jobs/{fine_tuning_job_id}/cancel")\n    Single<FineTuningJob> cancelFineTuningJob(@Path("fine_tuning_job_id") String fineTuningJobId);\n    @GET("/v1/fine_tuning/jobs/{fine_tuning_job_id}/events")\n    Single<OpenAiResponse<FineTuningEvent>> listFineTuningJobEvents(@Path("fine_tuning_job_id") String fineTuningJobId);\n    @Deprecated\n    @POST("/v1/fine-tunes")\n    Single<FineTuneResult> createFineTune(@Body FineTuneRequest request);\n    @POST("/v1/completions")\n    Single<CompletionResult> createFineTuneCompletion(@Body CompletionRequest request);\n    @Deprecated\n    @GET("/v1/fine-tunes")\n    Single<OpenAiResponse<FineTuneResult>> listFineTunes();\n    @Deprecated\n    @GET("/v1/fine-tunes/{fine_tune_id}")\n    Single<FineTuneResult> retrieveFineTune(@Path("fine_tune_id") String fineTuneId);\n    @Deprecated\n    @POST("/v1/fine-tunes/{fine_tune_id}/cancel")\n    Single<FineTuneResult> cancelFineTune(@Path("fine_tune_id") String fineTuneId);\n    @Deprecated\n    @GET("/v1/fine-tunes/{fine_tune_id}/events")\n    Single<OpenAiResponse<FineTuneEvent>> listFineTuneEvents(@Path("fine_tune_id") String fineTuneId);\n    @DELETE("/v1/models/{fine_tune_id}")\n    Single<DeleteResult> deleteFineTune(@Path("fine_tune_id") String fineTuneId);\n    @POST("/v1/images/generations")\n    Single<ImageResult> createImage(@Body CreateImageRequest request);\n    @POST("/v1/images/edits")\n    Single<ImageResult> createImageEdit(@Body RequestBody requestBody);\n    @POST("/v1/images/variations")\n    Single<ImageResult> createImageVariation(@Body RequestBody requestBody);\n    @POST("/v1/audio/transcriptions")\n    Single<TranscriptionResult> createTranscription(@Body RequestBody requestBody);\n    @POST("/v1/audio/translations")\n    Single<TranslationResult> createTranslation(@Body RequestBody requestBody);\n    @POST("/v1/moderations")\n    Single<ModerationResult> createModeration(@Body ModerationRequest request);\n    @Deprecated\n    @GET("v1/engines")\n    Single<OpenAiResponse<Engine>> getEngines();\n    @Deprecated\n    @GET("/v1/engines/{engine_id}")\n    Single<Engine> getEngine(@Path("engine_id") String engineId);\n    /**\n     * Account information inquiry: It contains total amount (in US dollars) and other information.\n     *\n     * @return\n     */\n    @Deprecated\n    @GET("v1/dashboard/billing/subscription")\n    Single<Subscription> subscription();\n    /**\n     * Account call interface consumption amount inquiry.\n     * totalUsage = Total amount used by the account (in US cents).\n     *\n     * @param starDate\n     * @param endDate\n     * @return Consumption amount information.\n     */\n    @Deprecated\n    @GET("v1/dashboard/billing/usage")\n    Single<BillingUsage> billingUsage(@Query("start_date") LocalDate starDate, @Query("end_date") LocalDate endDate);\n}': {'pac_name': 'com.theokanning.openai.client', 'class_name_list': ['com.theokanning.openai.client.OpenAiApi'], 'func_name_dict': {'com.theokanning.openai.client.OpenAiApi': ['com.theokanning.openai.client.OpenAiApi.listModels', 'com.theokanning.openai.client.OpenAiApi.getModel_String', 'com.theokanning.openai.client.OpenAiApi.createCompletion_CompletionRequest', 'com.theokanning.openai.client.OpenAiApi.createCompletionStream_CompletionRequest', 'com.theokanning.openai.client.OpenAiApi.createChatCompletion_ChatCompletionRequest', 'com.theokanning.openai.client.OpenAiApi.createChatCompletionStream_ChatCompletionRequest', 'com.theokanning.openai.client.OpenAiApi.createCompletion_String_CompletionRequest', 'com.theokanning.openai.client.OpenAiApi.createEdit_EditRequest', 'com.theokanning.openai.client.OpenAiApi.createEdit_String_EditRequest', 'com.theokanning.openai.client.OpenAiApi.createEmbeddings_EmbeddingRequest', 'com.theokanning.openai.client.OpenAiApi.createEmbeddings_String_EmbeddingRequest', 'com.theokanning.openai.client.OpenAiApi.listFiles', 'com.theokanning.openai.client.OpenAiApi.uploadFile_RequestBody_MultipartBody', 'com.theokanning.openai.client.OpenAiApi.deleteFile_String', 'com.theokanning.openai.client.OpenAiApi.retrieveFile_String', 'com.theokanning.openai.client.OpenAiApi.retrieveFileContent_String', 'com.theokanning.openai.client.OpenAiApi.createFineTuningJob_FineTuningJobRequest', 'com.theokanning.openai.client.OpenAiApi.listFineTuningJobs', 'com.theokanning.openai.client.OpenAiApi.retrieveFineTuningJob_String', 'com.theokanning.openai.client.OpenAiApi.cancelFineTuningJob_String', 'com.theokanning.openai.client.OpenAiApi.listFineTuningJobEvents_String', 'com.theokanning.openai.client.OpenAiApi.createFineTune_FineTuneRequest', 'com.theokanning.openai.client.OpenAiApi.createFineTuneCompletion_CompletionRequest', 'com.theokanning.openai.client.OpenAiApi.listFineTunes', 'com.theokanning.openai.client.OpenAiApi.retrieveFineTune_String', 'com.theokanning.openai.client.OpenAiApi.cancelFineTune_String', 'com.theokanning.openai.client.OpenAiApi.listFineTuneEvents_String', 'com.theokanning.openai.client.OpenAiApi.deleteFineTune_String', 'com.theokanning.openai.client.OpenAiApi.createImage_CreateImageRequest', 'com.theokanning.openai.client.OpenAiApi.createImageEdit_RequestBody', 'com.theokanning.openai.client.OpenAiApi.createImageVariation_RequestBody', 'com.theokanning.openai.client.OpenAiApi.createTranscription_RequestBody', 'com.theokanning.openai.client.OpenAiApi.createTranslation_RequestBody', 'com.theokanning.openai.client.OpenAiApi.createModeration_ModerationRequest', 'com.theokanning.openai.client.OpenAiApi.getEngines', 'com.theokanning.openai.client.OpenAiApi.getEngine_String', 'com.theokanning.openai.client.OpenAiApi.subscription', 'com.theokanning.openai.client.OpenAiApi.billingUsage_LocalDate_LocalDate']}, 'import_pac_name_list': ['com.theokanning.openai.DeleteResult', 'com.theokanning.openai.OpenAiResponse', 'com.theokanning.openai.audio.TranscriptionResult', 'com.theokanning.openai.audio.TranslationResult', 'com.theokanning.openai.billing.BillingUsage', 'com.theokanning.openai.billing.Subscription', 'com.theokanning.openai.completion.CompletionRequest', 'com.theokanning.openai.completion.CompletionResult', 'com.theokanning.openai.completion.chat.ChatCompletionRequest', 'com.theokanning.openai.completion.chat.ChatCompletionResult', 'com.theokanning.openai.edit.EditRequest', 'com.theokanning.openai.edit.EditResult', 'com.theokanning.openai.embedding.EmbeddingRequest', 'com.theokanning.openai.embedding.EmbeddingResult', 'com.theokanning.openai.engine.Engine', 'com.theokanning.openai.file.File', 'com.theokanning.openai.fine_tuning.FineTuningEvent', 'com.theokanning.openai.fine_tuning.FineTuningJob', 'com.theokanning.openai.fine_tuning.FineTuningJobRequest', 'com.theokanning.openai.finetune.FineTuneEvent', 'com.theokanning.openai.finetune.FineTuneRequest', 'com.theokanning.openai.finetune.FineTuneResult', 'com.theokanning.openai.image.CreateImageRequest', 'com.theokanning.openai.image.ImageResult', 'com.theokanning.openai.model.Model', 'com.theokanning.openai.moderation.ModerationRequest', 'com.theokanning.openai.moderation.ModerationResult', 'io.reactivex.Single', 'okhttp3.MultipartBody', 'okhttp3.RequestBody', 'okhttp3.ResponseBody', 'retrofit2.Call', 'retrofit2.http', 'java.time.LocalDate']}, '\npackage com.theokanning.openai;\n\n/**\n * OkHttp Interceptor that adds an authorization token header\n * \n * @deprecated Use {@link com.theokanning.openai.client.AuthenticationInterceptor}\n */\n@Deprecated\npublic class AuthenticationInterceptor extends com.theokanning.openai.client.AuthenticationInterceptor {\n\n    AuthenticationInterceptor(String token) {\n        super(token);\n    }\n\n}\n': {'pac_name': 'com.theokanning.openai', 'class_name_list': ['com.theokanning.openai.AuthenticationInterceptor'], 'func_name_dict': {}, 'import_pac_name_list': []}}
