package com.example.springai.chatmemory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.client.advisor.SimpleLoggerAdvisor;
import org.springframework.ai.chat.client.advisor.vectorstore.VectorStoreChatMemoryAdvisor;
import org.springframework.ai.chat.memory.ChatMemory;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.stereotype.Service;

import lombok.extern.slf4j.Slf4j;

@Service
@Slf4j
public class VectorStoreChatMemoryService {
  private ChatClient chatClient;

  public VectorStoreChatMemoryService(
      @Qualifier("chatMemoryVectorStore") VectorStore vectorStore,
      ChatClient.Builder chatClientBuilder) {

    this.chatClient = chatClientBuilder
        .defaultAdvisors(
            VectorStoreChatMemoryAdvisor.builder(vectorStore).build(),
            new SimpleLoggerAdvisor()
          )
        .build();

  }

  public String chat(String userText, String conversationId) {
    String answer = chatClient.prompt()
        .user(userText)
        .advisors(advisorSpec -> advisorSpec.param(
            ChatMemory.CONVERSATION_ID, conversationId))
        .call()
        .content();
    return answer;
  }
}
