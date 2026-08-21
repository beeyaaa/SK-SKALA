package com.skala.stock.service;

import com.skala.stock.dto.StockDto;
import com.skala.stock.entity.Stock;
import com.skala.stock.repository.StockRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class StockService {

    private final StockRepository stockRepository;

    @Transactional
    public StockDto createStock(StockDto stockDto) {
        if (stockRepository.existsByCode(stockDto.getCode())) {
            throw new RuntimeException("이미 존재하는 종목 코드입니다: " + stockDto.getCode());
        }

        Stock stock = Stock.builder()
                .code(stockDto.getCode())
                .name(stockDto.getName())
                .currentPrice(stockDto.getCurrentPrice())
                .previousPrice(stockDto.getPreviousPrice())
                .build();

        Stock savedStock = stockRepository.save(stock);
        return convertToDto(savedStock);
    }

    public StockDto getStockById(Long id) {
        Stock stock = stockRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("주식을 찾을 수 없습니다: " + id));
        return convertToDto(stock);
    }

    public List<StockDto> getAllStocks() {
        return stockRepository.findAll().stream()
                .map(this::convertToDto)
                .collect(Collectors.toList());
    }

    public StockDto getStockByCode(String code) {
        Stock stock = stockRepository.findByCode(code)
                .orElseThrow(() ->
                        new RuntimeException(
                                "주식을 찾을 수 없습니다: " + code
                        )
                );

        return convertToDto(stock);
    }

    private StockDto convertToDto(Stock stock) {
        return StockDto.builder()
                .id(stock.getId())
                .code(stock.getCode())
                .name(stock.getName())
                .currentPrice(stock.getCurrentPrice())
                .previousPrice(stock.getPreviousPrice())
                .build();
    }

    @Transactional
    public StockDto updateStock(
            Long id,
            StockDto stockDto) {

        Stock stock = stockRepository.findById(id)
                .orElseThrow(() ->
                        new RuntimeException(
                                "주식을 찾을 수 없습니다: " + id
                        )
                );

        if (!stock.getCode().equals(stockDto.getCode())
                && stockRepository.existsByCode(stockDto.getCode())) {

            throw new RuntimeException(
                    "이미 존재하는 종목 코드입니다: "
                            + stockDto.getCode()
            );
        }

        stock.setCode(stockDto.getCode());
        stock.setName(stockDto.getName());
        stock.setCurrentPrice(stockDto.getCurrentPrice());
        stock.setPreviousPrice(stockDto.getPreviousPrice());

        Stock updatedStock = stockRepository.save(stock);

        return convertToDto(updatedStock);
    }

    @Transactional
    public void deleteStock(Long id) {
        Stock stock = stockRepository.findById(id)
                .orElseThrow(() ->
                        new RuntimeException(
                                "주식을 찾을 수 없습니다: " + id
                        )
                );

        stockRepository.delete(stock);
    }

    
}
