package com.skala.skala_shop_api.common;

import java.nio.charset.StandardCharsets;
import java.security.Key;
import java.util.Arrays;
import java.util.Date;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import com.skala.skala_shop_api.exception.Error;
import com.skala.skala_shop_api.exception.ResponseException;

import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.security.Keys;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

@Component
public class SessionHandler {

    private static final String ACCESS_TOKEN_COOKIE = "bff-access";

    private final HttpServletRequest request;
    private final HttpServletResponse response;
    private final Key signingKey;
    private final long expirationMillis;

    public SessionHandler(
            HttpServletRequest request,
            HttpServletResponse response,
            @Value("${jwt.secret:skala-shop-api-secret-key-must-be-at-least-32-bytes}") String secret,
            @Value("${jwt.expiration-millis:3600000}") long expirationMillis) {
        this.request = request;
        this.response = response;
        this.signingKey = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
        this.expirationMillis = expirationMillis;
    }

    // 로그인한 고객 ID를 담은 JWT를 HttpOnly Cookie로 전달
    public void storeAccessToken(String customerId) {
        Date now = new Date();
        String token = Jwts.builder()
                .setSubject(customerId)
                .setIssuedAt(now)
                .setExpiration(new Date(now.getTime() + expirationMillis))
                .signWith(signingKey, SignatureAlgorithm.HS256)
                .compact();

        Cookie cookie = new Cookie(ACCESS_TOKEN_COOKIE, token);
        cookie.setHttpOnly(true);
        cookie.setPath("/");
        cookie.setMaxAge((int) (expirationMillis / 1000));
        response.addCookie(cookie);
    }

    // 요청 Cookie의 JWT를 검증하고 로그인한 고객 ID 반환
    public String getCustomerId() {
        Cookie[] cookies = request.getCookies();
        if (cookies == null) {
            throw new ResponseException(Error.SESSION_NOT_FOUND);
        }

        String token = Arrays.stream(cookies)
                .filter(cookie -> ACCESS_TOKEN_COOKIE.equals(cookie.getName()))
                .map(Cookie::getValue)
                .findFirst()
                .orElseThrow(() -> new ResponseException(Error.SESSION_NOT_FOUND));

        try {
            return Jwts.parserBuilder()
                    .setSigningKey(signingKey)
                    .build()
                    .parseClaimsJws(token)
                    .getBody()
                    .getSubject();
        } catch (JwtException | IllegalArgumentException exception) {
            throw new ResponseException(Error.SESSION_NOT_FOUND);
        }
    }
}
