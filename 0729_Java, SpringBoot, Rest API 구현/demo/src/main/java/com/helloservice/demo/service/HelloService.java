package com.helloservice.demo.service;
import org.springframework.stereotype.Service;
import com.helloservice.demo.data.HelloResponse;

@Service

public class HelloService {
    public HelloResponse createMessage(String name) {
        HelloResponse response = new HelloResponse();
        response.setMessage("안녕하세요, " + name + "님!");
        return response;
}
}