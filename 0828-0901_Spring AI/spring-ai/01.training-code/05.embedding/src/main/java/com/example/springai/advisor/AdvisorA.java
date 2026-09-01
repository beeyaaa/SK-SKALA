package com.example.springai.advisor;

import org.springframework.ai.chat.client.ChatClientRequest;
import org.springframework.ai.chat.client.ChatClientResponse;
import org.springframework.ai.chat.client.advisor.api.CallAdvisor;
import org.springframework.ai.chat.client.advisor.api.CallAdvisorChain;

import org.springframework.core.Ordered;

public class AdvisorA implements CallAdvisor {
  @Override
  public String getName() {
    return this.getClass().getSimpleName();
  }

  @Override
  public int getOrder() {
    return Ordered.LOWEST_PRECEDENCE - 1;
  }

  @Override
  public ChatClientResponse adviseCall(ChatClientRequest request, CallAdvisorChain chain) {
    System.out.println("[전처리] AdvisorA");
    ChatClientResponse response = chain.nextCall(request);
    System.out.println("[후처리] AdvisorA");
    return response;
  }
}





