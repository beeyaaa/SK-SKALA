package com.example.springai.chatmemory;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.client.advisor.MessageChatMemoryAdvisor;
import org.springframework.ai.chat.client.advisor.SimpleLoggerAdvisor;
import org.springframework.ai.chat.memory.ChatMemory;
import org.springframework.ai.chat.memory.MessageWindowChatMemory;
import org.springframework.stereotype.Service;

import lombok.extern.slf4j.Slf4j;

@Service
@Slf4j
public class MessageWindowChatMemoryService {
  private ChatClient chatClient;
  
  public MessageWindowChatMemoryService( ChatClient.Builder chatClientBuilder) {  
      // ChatMemory 구현체를 직접 생성하여 MessageChatMemoryAdvisor에 전달
      // 최근 10개의 메시지만 유지하는 윈도우 방식 채팅 메모리 
      MessageWindowChatMemory messageWindowChatMemory = MessageWindowChatMemory.builder()
          .maxMessages(10)
          .build();

      this.chatClient = chatClientBuilder
          .defaultAdvisors(
              MessageChatMemoryAdvisor.builder(messageWindowChatMemory).build(),
              new SimpleLoggerAdvisor()
          )
          .build();
  }
  
  
  public String chat(String userText, String conversationId) {
    String answer = chatClient.prompt()
      .user(userText)
      .advisors(advisorSpec -> advisorSpec.param(ChatMemory.CONVERSATION_ID, conversationId))
      .call()
      .content();
    return answer;
  }
}
