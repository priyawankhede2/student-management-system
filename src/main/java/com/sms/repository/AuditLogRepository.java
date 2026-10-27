package com.sms.repository;

import com.sms.entity.AuditLog;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface AuditLogRepository extends JpaRepository<AuditLog, Long> {
    List<AuditLog> findTop50ByOrderByOccurredAtDesc();
    List<AuditLog> findByActionOrderByOccurredAtDesc(String action);
}
