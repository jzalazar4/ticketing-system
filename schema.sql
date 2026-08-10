-- Main table for tickets
CREATE TABLE IF NOT EXISTS tickets (
    ticket_id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Message table for ticket communications
CREATE TABLE IF NOT EXISTS ticket_messages (
    message_id VARCHAR(50) PRIMARY KEY,
    ticket_id VARCHAR(50) REFERENCES tickets(ticket_id),
    message_text TEXT NOT NULL,
    author VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Initial data insertion for tickets and messages
INSERT INTO tickets (ticket_id, title, status, created_by) VALUES 
    ('t-1', 'Fail to login', 'open', 'ana@example.com'),
    ('t-2', 'Fail in data pipeline', 'in_progress', 'carlos@example.com'),
    ('t-3', 'Access request to Lakebase', 'resolved', 'maria@example.com');

INSERT INTO ticket_messages (message_id, ticket_id, message_text, author) VALUES 
    ('m-1', 't-1', 'Cannot login with credentials.', 'ana@example.com'),
    ('m-2', 't-1', 'Support received the request.', 'soporte@example.com'),
    ('m-3', 't-2', 'The Databricks job fails at midnight.', 'carlos@example.com');
;