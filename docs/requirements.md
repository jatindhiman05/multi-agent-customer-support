# Multi-Agent Customer Support System

## 1. Project Overview

This project implements a production-oriented multi-agent customer support
system for a fictional e-commerce company.

The system will allow customers to interact with an AI support assistant
capable of answering questions, retrieving customer-specific information,
performing permitted business operations, troubleshooting products, and
escalating conversations to human support when necessary.

The project will simulate the backend systems of a real e-commerce company
while keeping the primary focus on customer support.

---

## 2. Core Customer Support Domains

### 2.1 Orders

Customers should be able to:

- View their orders
- Retrieve a specific order
- Check order status
- View items in an order
- Cancel eligible orders
- Request permitted order modifications

Example requests:

- "Where is my order?"
- "Show me my latest order."
- "What did I order?"
- "Cancel order ORD-1001."
- "Can I change my delivery address?"

---

### 2.2 Shipping and Delivery

Customers should be able to:

- Track shipments
- View estimated delivery dates
- View tracking history
- Report delayed deliveries
- Report missing packages
- Report packages marked delivered but not received

Example requests:

- "Where is my package?"
- "When will my order arrive?"
- "Why is my shipment delayed?"
- "My order says delivered but I haven't received it."

---

### 2.3 Returns and Refunds

Customers should be able to:

- Check return eligibility
- Request a return
- Check return status
- Check refund status
- Understand applicable return/refund policies

Example requests:

- "Can I return my earbuds?"
- "I received the wrong item."
- "Where is my refund?"
- "How long do refunds take?"

---

### 2.4 Payments

Customers should be able to receive assistance with:

- Payment status
- Failed payments
- Duplicate charges
- Refund-related payment information
- Invoice information

Example requests:

- "Why did my payment fail?"
- "I was charged twice."
- "Was my payment successful?"
- "Can I get an invoice?"

The AI must never directly handle or expose sensitive payment credentials
such as full card numbers or CVVs.

---

### 2.5 Products

Customers should be able to:

- Ask about product specifications
- Check product availability
- Ask about compatibility
- Ask about warranties
- Compare relevant product information

Example requests:

- "Does this charger support fast charging?"
- "Is this power bank in stock?"
- "Is this case compatible with my phone?"
- "How long is the warranty?"

---

### 2.6 Technical Support

Customers should receive troubleshooting assistance for supported products.

Example requests:

- "My earbuds won't connect."
- "My speaker keeps disconnecting."
- "My power bank isn't charging."

The system may retrieve troubleshooting documentation and guide the customer
through multiple diagnostic steps.

Cases that cannot be resolved automatically may be escalated to human
support.

---

### 2.7 Customer Accounts

Customers should receive assistance with:

- Account information
- Saved addresses
- Account settings
- Login problems
- Password-reset guidance
- Account deletion requests

Sensitive account operations must require appropriate authentication and
authorization.

---

### 2.8 Company Policies and General Questions

The system should answer questions regarding:

- Return policies
- Refund policies
- Shipping policies
- Warranty policies
- Payment methods
- Support hours
- Frequently asked questions
- General company information

These answers should be grounded in the company's knowledge base rather than
invented by the language model.

---

### 2.9 Human Escalation

The system must support escalation to a human support representative.

Possible escalation conditions include:

- Customer explicitly requests a human
- Repeated automated resolution failures
- Sensitive or high-risk situations
- Operations requiring human authorization
- Unsupported requests
- Cases where the AI cannot confidently or safely proceed

The system should preserve relevant conversation context when creating an
escalation.

---

## 3. Data Categories

The system will work with two fundamentally different categories of data.

### 3.1 Operational Data

Operational data represents changing business state.

Examples:

- Customers
- Products
- Inventory
- Orders
- Order items
- Payments
- Shipments
- Tracking events
- Returns
- Refunds
- Support tickets

Operational data will eventually be stored in PostgreSQL and accessed
through controlled application services and tools.

The language model should not have unrestricted direct database access.

---

### 3.2 Knowledge Data

Knowledge data represents relatively static company information.

Examples:

- FAQs
- Policies
- Product documentation
- Troubleshooting guides
- Warranty information
- Company information

Knowledge data will be accessed through a retrieval-augmented generation
(RAG) pipeline.

---

## 4. High-Level AI Responsibilities

The AI system should eventually be capable of:

1. Understanding the customer's request.
2. Determining which support domain is responsible.
3. Retrieving relevant company knowledge when required.
4. Calling authorized business tools when live data is required.
5. Combining information from multiple sources when necessary.
6. Maintaining conversation context.
7. Asking for clarification when required.
8. Requesting confirmation before sensitive actions.
9. Refusing unauthorized operations.
10. Escalating appropriate cases to human support.

---

## 5. Safety and Authorization Principles

The system must follow several core principles.

### Customer Isolation

A customer must only be able to access resources they are authorized to
access.

For example, knowing another customer's order ID must not provide access to
that order.

### Least Privilege

Agents should only receive access to the tools required for their domain.

### Controlled Actions

Sensitive or destructive operations must pass through deterministic business
logic rather than relying solely on an LLM decision.

### Confirmation

Operations such as cancelling an order or initiating certain account changes
may require explicit customer confirmation before execution.

### Auditability

Important actions should eventually be logged so that the system can explain
what action occurred, when it occurred, and which authenticated customer
requested it.

---

## 6. Initial Business Entities

The initial e-commerce domain will contain:

- Customer
- Product
- Order
- Order Item
- Payment
- Shipment
- Tracking Event
- Return
- Refund
- Support Ticket

These entities will form the basis of the initial PostgreSQL database design.

---

## 7. Out of Scope for the Initial Version

The first version will not attempt to build a complete e-commerce platform.

The following systems are initially outside the project's scope:

- Recommendation systems
- Supplier management
- Warehouse optimization
- Delivery route optimization
- Marketplace sellers
- Advertising systems
- Advanced fraud detection
- Full checkout implementation

They may be simulated or integrated later if required by customer-support
workflows.

---

## 8. Long-Term Architecture Direction

The project is expected to evolve toward:

Customer
→ API
→ AI orchestration
→ specialized support agents
→ controlled tools / RAG
→ business services
→ databases and external systems

Potential specialized agents include:

- Order Agent
- Payment/Refund Agent
- Knowledge Agent
- Technical Support Agent
- Account Agent
- Human Escalation workflow

The exact multi-agent architecture will be introduced only after the
underlying business services, tools, and retrieval systems are functional.