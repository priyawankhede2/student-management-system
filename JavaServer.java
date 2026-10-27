import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpExchange;

import java.io.*;
import java.net.InetSocketAddress;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

/**
 * Native Java 21 HTTP Runner for Student Management System.
 * Can be run directly without Maven:
 *    java JavaServer.java
 */
public class JavaServer {

    private static final int PORT = 8080;
    private static final Path STATIC_DIR = Paths.get("app", "static");
    private static final Path LOG_FILE = Paths.get("app", "sms.log");

    public static void main(String[] args) throws IOException {
        HttpServer server = HttpServer.create(new InetSocketAddress(PORT), 0);
        
        server.createContext("/", new StaticAndApiHandler());
        server.setExecutor(null); // default executor

        logInfo("Java 21 Student Management System started on http://localhost:" + PORT + "/");
        System.out.println("============================================================");
        System.out.println("  Java 21 - Student Management System (Google UI)");
        System.out.println("  URL: http://localhost:" + PORT + "/");
        System.out.println("  Log: " + LOG_FILE.toAbsolutePath());
        System.out.println("============================================================");

        server.start();
    }

    static class StaticAndApiHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            String path = exchange.getRequestURI().getPath();
            if (path.equals("/")) {
                path = "/index.html";
            }

            Path filePath = STATIC_DIR.resolve(path.substring(1)).normalize();

            // Check if file exists in static directory
            if (Files.exists(filePath) && !Files.isDirectory(filePath)) {
                String contentType = Files.probeContentType(filePath);
                if (contentType == null) {
                    if (path.endsWith(".css")) contentType = "text/css";
                    else if (path.endsWith(".js")) contentType = "application/javascript";
                    else if (path.endsWith(".html")) contentType = "text/html";
                    else contentType = "application/octet-stream";
                }

                byte[] bytes = Files.readAllBytes(filePath);
                exchange.getResponseHeaders().set("Content-Type", contentType);
                exchange.getResponseHeaders().set("Access-Control-Allow-Origin", "*");
                exchange.sendResponseHeaders(200, bytes.length);
                OutputStream os = exchange.getResponseBody();
                os.write(bytes);
                os.close();
            } else {
                // Fallback to index.html for SPA routes
                Path indexPath = STATIC_DIR.resolve("index.html");
                if (Files.exists(indexPath)) {
                    byte[] bytes = Files.readAllBytes(indexPath);
                    exchange.getResponseHeaders().set("Content-Type", "text/html; charset=utf-8");
                    exchange.getResponseHeaders().set("Access-Control-Allow-Origin", "*");
                    exchange.sendResponseHeaders(200, bytes.length);
                    OutputStream os = exchange.getResponseBody();
                    os.write(bytes);
                    os.close();
                } else {
                    String msg = "404 Not Found";
                    exchange.sendResponseHeaders(404, msg.length());
                    OutputStream os = exchange.getResponseBody();
                    os.write(msg.getBytes());
                    os.close();
                }
            }
        }
    }

    private static void logInfo(String message) {
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss,SSS"));
        String line = timestamp + " [INFO] [Java21-Server] " + message + "\n";
        try {
            if (!Files.exists(LOG_FILE.getParent())) {
                Files.createDirectories(LOG_FILE.getParent());
            }
            Files.writeString(LOG_FILE, line, java.nio.file.StandardOpenOption.CREATE, java.nio.file.StandardOpenOption.APPEND);
        } catch (IOException ignored) {}
    }
}
