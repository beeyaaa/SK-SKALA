package com.example.springai.tools;

import java.time.LocalDateTime;

import org.springframework.ai.tool.annotation.Tool;
import org.springframework.context.i18n.LocaleContextHolder;
import org.springframework.stereotype.Component;

import lombok.extern.slf4j.Slf4j;

@Component
@Slf4j
public class DateTimeTools {
  @Tool(description = "사용자의 시간대에 맞는 현재 날짜와 시간 정보를 제공합니다.")
  public String getCurrentDateTime() {
    log.info ("getCurrentDateTime() 호출됨");
    String nowTime = LocalDateTime.now()
            .atZone(LocaleContextHolder.getTimeZone().toZoneId())
            .toString();
    log.info("현재 시간: {}", nowTime);
    return nowTime;
  }
}
