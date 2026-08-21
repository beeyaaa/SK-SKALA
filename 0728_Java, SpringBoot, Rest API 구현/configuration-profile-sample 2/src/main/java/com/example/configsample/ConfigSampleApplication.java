package com.example.configsample;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

@SpringBootApplication
@ConfigurationPropertiesScan
public class ConfigSampleApplication {

    public static void main(String[] args) {
        SpringApplication.run(ConfigSampleApplication.class, args);
    }
}
