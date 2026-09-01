package com.example.stdio;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * STDIO MCP Server Application
 * 
 * User와 Product 관리를 위한 MCP 도구를 제공하는 STDIO 기반 서버
 */
@SpringBootApplication
public class StdioMcpServerApplication {

    public static void main(String[] args) {
        SpringApplication.run(StdioMcpServerApplication.class, args);
    }

}
