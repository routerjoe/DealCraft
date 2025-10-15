-- Red River Sales Automation Configuration Schema
-- Strategic filtering and business intelligence rules

-- ============================================================================
-- CONFIGURATION TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS config_strategic_customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT UNIQUE NOT NULL,
    priority_level TEXT DEFAULT 'HIGH',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS config_value_thresholds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tier_name TEXT UNIQUE NOT NULL,
    min_value REAL NOT NULL,
    max_value REAL,
    action TEXT NOT NULL,
    priority_level TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS config_technology_verticals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vertical_name TEXT UNIQUE NOT NULL,
    priority_level TEXT DEFAULT 'MEDIUM',
    auto_flag BOOLEAN DEFAULT 1,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS config_oem_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    oem_name TEXT UNIQUE NOT NULL,
    currently_authorized BOOLEAN DEFAULT 0,
    tracking_start_date DATE,
    occurrence_count INTEGER DEFAULT 0,
    total_value_seen REAL DEFAULT 0,
    business_case_threshold INTEGER DEFAULT 5,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TRACKING TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS oem_occurrence_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    oem_name TEXT NOT NULL,
    rfq_id INTEGER,
    rfq_number TEXT,
    customer TEXT,
    estimated_value REAL,
    competition_level INTEGER,
    technology_vertical TEXT,
    occurred_at DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rfq_id) REFERENCES rfqs(id)
);

CREATE TABLE IF NOT EXISTS rfi_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rfq_id INTEGER,
    rfi_number TEXT,
    customer TEXT,
    responded BOOLEAN DEFAULT 0,
    response_date DATE,
    subsequent_rfq_received BOOLEAN DEFAULT 0,
    subsequent_rfq_number TEXT,
    awarded BOOLEAN DEFAULT 0,
    estimated_value REAL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rfq_id) REFERENCES rfqs(id)
);

CREATE TABLE IF NOT EXISTS late_rfq_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rfq_id INTEGER,
    rfq_number TEXT,
    received_date TIMESTAMP,
    deadline DATE,
    days_to_respond INTEGER,
    reason_late TEXT,
    pattern_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rfq_id) REFERENCES rfqs(id)
);

-- ============================================================================
-- INSERT STRATEGIC CUSTOMERS
-- ============================================================================

INSERT OR IGNORE INTO config_strategic_customers (customer_name, priority_level, notes) VALUES
('AFCENT', 'CRITICAL', 'Air Forces Central Command'),
('ARCENT', 'CRITICAL', 'Army Central Command'),
('US CYBERCOMMAND', 'CRITICAL', 'United States Cyber Command'),
('AFSOC', 'CRITICAL', 'Air Force Special Operations Command'),
('USSOCOM', 'CRITICAL', 'US Special Operations Command'),
('Space Force', 'CRITICAL', 'United States Space Force'),
('DARPA', 'CRITICAL', 'Defense Advanced Research Projects Agency'),
('AETC', 'HIGH', 'Air Education and Training Command'),
('Hill AFB', 'HIGH', 'Hill Air Force Base'),
('Eglin AFB', 'HIGH', 'Eglin Air Force Base'),
('Tyndall AFB', 'HIGH', 'Tyndall Air Force Base'),
('Patrick AFB', 'HIGH', 'Patrick Space Force Base'),
('Andrews AFB', 'HIGH', 'Joint Base Andrews'),
('Bolling AFB', 'HIGH', 'Joint Base Anacostia-Bolling'),
('AFOSI', 'HIGH', 'Air Force Office of Special Investigations');

-- ============================================================================
-- INSERT VALUE THRESHOLDS
-- ============================================================================

INSERT OR IGNORE INTO config_value_thresholds (tier_name, min_value, max_value, action, priority_level) VALUES
('TIER_1_CRITICAL', 1000000, NULL, 'IMMEDIATE_EXECUTIVE_NOTIFICATION', 'CRITICAL'),
('TIER_2_HIGH', 200000, 999999, 'SALES_TEAM_NOTIFICATION', 'HIGH'),
('TIER_3_REVIEW', 20000, 199999, 'FLAG_FOR_REVIEW', 'MEDIUM'),
('TIER_4_LOW', 0, 19999, 'STANDARD_PROCESS', 'LOW');

-- ============================================================================
-- INSERT TECHNOLOGY VERTICALS
-- ============================================================================

INSERT OR IGNORE INTO config_technology_verticals (vertical_name, priority_level, auto_flag, notes) VALUES
('Zero Trust', 'HIGH', 1, 'Strategic priority - always flag'),
('Data Center', 'HIGH', 1, 'Core competency - always flag'),
('Enterprise Networking', 'HIGH', 1, 'Core competency - always flag'),
('Cybersecurity', 'HIGH', 1, 'Growing vertical'),
('Cloud Migration', 'MEDIUM', 1, 'Emerging opportunity'),
('AI/ML Infrastructure', 'MEDIUM', 1, 'Future growth area'),
('SIEM/Security Analytics', 'MEDIUM', 1, 'Tracking for new business'),
('SD-WAN', 'MEDIUM', 1, 'Network modernization'),
('Hybrid Cloud', 'MEDIUM', 1, 'Infrastructure trend');

-- ============================================================================
-- INSERT OEM TRACKING (New Business Opportunities)
-- ============================================================================

INSERT OR IGNORE INTO config_oem_tracking (oem_name, currently_authorized, business_case_threshold, notes) VALUES
('Atlassian', 0, 5, 'DevOps/Collaboration - tracking frequency'),
('Graylog', 0, 5, 'SIEM - security analytics opportunity'),
('LogRhythm', 0, 5, 'SIEM - security analytics opportunity'),
('Sparx', 0, 8, 'Niche - enterprise architecture'),
('Quest/Toad', 0, 5, 'Database tools - moderate opportunity');

-- ============================================================================
-- INSERT OEM TRACKING (Currently Authorized)
-- ============================================================================

INSERT OR IGNORE INTO config_oem_tracking (oem_name, currently_authorized, notes) VALUES
('Cisco', 1, 'Core partner - enterprise networking'),
('Palo Alto Networks', 1, 'Core partner - cybersecurity'),
('Dell/EMC', 1, 'Storage and infrastructure'),
('NetApp', 1, 'Storage solutions'),
('F5 Networks', 1, 'Application delivery'),
('Microsoft', 1, 'Cloud and software'),
('VMware', 1, 'Virtualization'),
('Red Hat', 1, 'Open source / cloud infrastructure');

-- ============================================================================
-- VIEWS FOR REPORTING
-- ============================================================================

CREATE VIEW IF NOT EXISTS v_strategic_rfqs AS
SELECT 
    r.*,
    sc.priority_level as customer_priority,
    CASE 
        WHEN r.estimated_value >= 1000000 THEN 'TIER_1_CRITICAL'
        WHEN r.estimated_value >= 200000 THEN 'TIER_2_HIGH'
        WHEN r.estimated_value >= 20000 THEN 'TIER_3_REVIEW'
        ELSE 'TIER_4_LOW'
    END as value_tier
FROM rfqs r
LEFT JOIN config_strategic_customers sc ON r.customer LIKE '%' || sc.customer_name || '%'
WHERE sc.customer_name IS NOT NULL OR r.estimated_value >= 20000;

CREATE VIEW IF NOT EXISTS v_oem_business_case_90d AS
SELECT 
    o.oem_name,
    o.occurrence_count,
    o.total_value_seen,
    o.business_case_threshold,
    COUNT(DISTINCT log.rfq_id) as occurrences_90d,
    SUM(log.estimated_value) as total_value_90d,
    COUNT(DISTINCT log.customer) as unique_customers_90d,
    AVG(log.competition_level) as avg_competition
FROM config_oem_tracking o
LEFT JOIN oem_occurrence_log log ON o.oem_name = log.oem_name 
    AND log.occurred_at >= date('now', '-90 days')
WHERE o.currently_authorized = 0
GROUP BY o.oem_name
ORDER BY occurrences_90d DESC, total_value_90d DESC;

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_oem_occurrence_log_date ON oem_occurrence_log(occurred_at);
CREATE INDEX IF NOT EXISTS idx_oem_occurrence_log_oem ON oem_occurrence_log(oem_name);
CREATE INDEX IF NOT EXISTS idx_rfi_tracking_customer ON rfi_tracking(customer);
CREATE INDEX IF NOT EXISTS idx_late_rfq_tracking_date ON late_rfq_tracking(received_date);
