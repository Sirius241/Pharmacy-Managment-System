
CREATE DATABASE PharmacyManagement;
USE PharmacyManagement;
create table customer (
C_ID INT PRIMARY KEY AUTO_INCREMENT,
C_name VARCHAR(100) NOT NULL,
Age INT,
Sex VARCHAR(10),
Address TEXT,
Pwd VARCHAR(255) NOT NULL,
EmailID VARCHAR(100) UNIQUE
  );
  CREATE TABLE CustomerPhone (
    C_ID INT,
    Ph_no VARCHAR(15),
    PRIMARY KEY (C_ID, Ph_no),
    FOREIGN KEY (C_ID) REFERENCES Customer(C_ID) ON DELETE CASCADE
);
CREATE TABLE Drugs (
    D_ID INT PRIMARY KEY AUTO_INCREMENT,
    D_name VARCHAR(100) NOT NULL,
    Mnf_date DATE,
    Expiry_date DATE,
    D_use TEXT,
    C_ID INT, 
    FOREIGN KEY (C_ID) REFERENCES Customer(C_ID) ON DELETE SET NULL
);
CREATE TABLE Manager (
    M_ID INT PRIMARY KEY AUTO_INCREMENT,
    M_name VARCHAR(100) NOT NULL,
    Ph_no VARCHAR(15) UNIQUE,
    M_pwd VARCHAR(255) NOT NULL
);
CREATE TABLE Supplier (
    S_ID INT PRIMARY KEY AUTO_INCREMENT,
    S_name VARCHAR(100) NOT NULL,
    S_address TEXT,
    S_phone VARCHAR(15),
    M_ID INT,
    FOREIGN KEY (M_ID) REFERENCES Manager(M_ID) ON DELETE SET NULL
);
CREATE TABLE Sales (
    Sale_ID INT PRIMARY KEY AUTO_INCREMENT,
    Total_amt DECIMAL(10,2) NOT NULL,
    Date DATE,
    Time TIME,
    M_ID INT,
    FOREIGN KEY (M_ID) REFERENCES Manager(M_ID) ON DELETE SET NULL
);
CREATE TABLE Inventory (
    Rem_qty INT NOT NULL,
    D_ID INT,
    M_ID INT,
    PRIMARY KEY (D_ID, M_ID),
    FOREIGN KEY (D_ID) REFERENCES Drugs(D_ID) ON DELETE CASCADE,
    FOREIGN KEY (M_ID) REFERENCES Manager(M_ID) ON DELETE CASCADE
);
CREATE TABLE Orders (
    Order_ID INT PRIMARY KEY AUTO_INCREMENT,
    C_ID INT,
    Qty INT NOT NULL,
    Name VARCHAR(100),
    Item VARCHAR(100),
    FOREIGN KEY (C_ID) REFERENCES Customer(C_ID) ON DELETE CASCADE
);
CREATE TABLE Supplies (
    D_ID INT,
    S_ID INT,
    Qty INT NOT NULL,
    PRIMARY KEY (D_ID, S_ID),
    FOREIGN KEY (D_ID) REFERENCES Drugs(D_ID) ON DELETE CASCADE,
    FOREIGN KEY (S_ID) REFERENCES Supplier(S_ID) ON DELETE CASCADE
);
CREATE TABLE Sale_Item (
    D_ID INT,
    S_ID INT,
    Sale_qty INT NOT NULL,
    Total_price DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (D_ID, S_ID),
    FOREIGN KEY (D_ID) REFERENCES Drugs(D_ID) ON DELETE CASCADE,
    FOREIGN KEY (S_ID) REFERENCES Supplier(S_ID) ON DELETE CASCADE
);

INSERT INTO Customer (C_name, Age, Sex, Address, Pwd, EmailID) 
VALUES 
('Kritika P', 30, 'Female', '123 Vijaynagar,Blore', 'kp123', 'kp@example.com'),
('Ram G', 40, 'Male', '456 Kengeri,Blore', 'rg456', 'rg@example.com');
INSERT INTO Customer (C_name, Age, Sex, Address, Pwd, EmailID) 
VALUES 
('Amith',25,'Male','srinagar','am123','am@gmail.com'),
('Rani',55,'Female','Jayanagar','r123','r@gmail.com'),
('Ravi',65,'Male','HSR','ra456','ravi@bing.com');
INSERT INTO CustomerPhone (C_ID, Ph_no) 
VALUES 
(1, '123-456-7890'), 
(1, '987-654-3210'), 
(2, '111-222-3333');
INSERT INTO Drugs (D_name, Mnf_date, Expiry_date, D_use, C_ID) 
VALUES 
('Paracetamol', '2024-01-01', '2026-01-01', 'Pain Reliever', 1),
('Aspirin', '2023-06-15', '2025-06-15', 'Anti-inflammatory', 2);
INSERT INTO Drugs (D_name, Mnf_date, Expiry_date, D_use, C_ID) 
VALUES 
('Cetirizine', '2023-03-01', '2025-03-01', 'Antihistamine', 1),  -- Associated with Customer ID 1
('Ibuprofen', '2023-04-01', '2025-04-01', 'Anti-inflammatory', 2),  -- Associated with Customer ID 2
('Amoxicillin', '2023-05-01', '2025-05-01', 'Antibiotic', 1); 
INSERT INTO Manager (M_name, Ph_no, M_pwd) 
VALUES 
('David Warner', '555-888-9999', 'davidpass');
INSERT INTO Manager (M_name, Ph_no, M_pwd) 
VALUES 
('Warner', '545-678-9369', 'warnerpass');
INSERT INTO Supplier (S_name, S_address, S_phone, M_ID) 
VALUES 
('MedLife Inc.', '789 RR Nagar,Mysore', '555-555-5555', 1);
INSERT INTO Orders (C_ID, Qty, Name, Item) 
VALUES 
(1, 2, 'Pain Relief Pack', 'Paracetamol'),
(2, 1, 'Headache Relief', 'Aspirin');
INSERT INTO Orders (C_ID, Qty, Name, Item) 
VALUES 
(1, 2, 'Cold Relief Pack', 'Cetirizine'),   -- 2 units of Cetirizine ordered by Customer 1
(3, 5, 'Fever Medicine', 'Ibuprofen'),      -- 5 units of Ibuprofen ordered by Customer 3
(2, 3, 'Antibiotic Course', 'Amoxicillin'); -- 3 units of Amoxicillin ordered by Customer 2
INSERT INTO Sales (Total_amt, Date, Time, M_ID)
VALUES
(150.00, '2025-02-04', '14:30:00', 1),  -- Sale by Manager with M_ID = 1
(200.00, '2025-02-24', '11:00:00', 2),  -- Sale by Manager with M_ID = 2
(120.00, '2025-02-20', '16:00:00', 1),  -- Sale by Manager with M_ID = 1
(250.00, '2025-02-24', '10:30:40', 2),  -- Sale by Manager with M_ID = 2
(180.00, '2025-02-22', '18:00:00', 1);  -- Sale by Manager with M_ID = 1


insert into Inventory (Rem_qty, D_ID, M_ID)
VALUES
(10, 1, 1),  -- Drug 1 (e.g., 'Paracetamol') managed by Manager 1
(50, 2, 2),   -- Drug 2 (e.g., 'Aspirin') managed by Manager 2
(75, 3, 1),   -- Drug 3 (e.g., 'Cetirizine') managed by Manager 1
(1, 4, 2),   -- Drug 4 (e.g., 'Ibuprofen') managed by Manager 2
(1, 5, 1);   -- Drug 5 (e.g., 'Amoxicillin') managed by Manager 1


 update customer set pwd="Kp123456" where c_id=1;
 update supplier set S_phone='656650879' where S_ID=7;
 
 select * from customer;
















  
  