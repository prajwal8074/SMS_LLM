# Enabling easy LLM and Marketplace access to Farmers and those unfamiliar with Modern Tech

### This project empowers farmers and tech-unfamiliar individuals by providing easy access to LLMs and an online marketplace via phone calls. Users simply talk to an AI in their local language to list products, get orders, and fulfill them. Authentication is simplified, using only a salted hashed phone number, with the call itself serving as verification. This brings the power of AI and e-commerce to everyone, no complex tech needed.

## Milestone Plan

- **Week 1 Ideation and Setup**
  - [x] Discussion: [Minutes of Discussion](docs/Minutes-of-Discussion/README.md)
  - [x] Ideas:
    - ✅ [SMS LLM](docs/SMS_LLM.pdf)
    - ❌ [Marketplace MCP](docs/MarketplaceMCP.pdf)
  - [x] Initial Plan: [6 week plan](docs/6_week_plan.pdf)
  - [x] Research Results: [Indian Languages Translation Model](docs/Translate-100-languages) [Text To Speech Model](docs/Text-To-Speech-Unlimited) <p align="right">(**Aditya**)</p>
  - [x] Setup: [Call Interface Setup](Call-Interface/README.md) <p align="right">(**Prajwal**)</p>

- **Week 2 Core Infrastructure**
  - [x] Integrate API gateway with call interface, [Check Demo](Call-Interface) <p align="right">(**Prajwal**)</p>
  - [x] [AWS Setup](AWS) 
    - [x] Pre-trained LLM API(Gemini 2.5 Flash) and language translation <p align="right">(**Aditya**)</p>
    - [x] Speech language detection for language translation model <p align="right">(**Aditya**)</p>
    - [x] Basic speech-to-text and text to speech <p align="right">(**Shubham**)</p>
    - [x] Integration of all models <p align="right">(**Shubham**)</p>
    - [x] Reproducibility of AWS Setup using AWS CloudFormation <p align="right">(**Shubham**)</p>
  - [x] In Depth testing of the Lambda Function <p align="right">(**Akash**)</p>

- **Week 3 MCP Server & Caching**
  - [ ] Create a simple marketplace where session login is done using an active phone call and user id is salted hashed phone number <p align="right">(**Shubham**)</p>
  - [ ] Set up CI/CD pipeline on github focusing on marketplace security <p align="right">(**Akash**)</p>
  - [ ] Simple caching system & FAQ database for common farming questions <p align="right">(**Aditya**)</p>
  - [ ] Create an MCP Server for the marketplace <p align="right">(**Prajwal**)</p>

- **Week 4 Buffer Week 1**
  
- **Week 5 Pilot Launch**
  - [ ] Basic analytics tracking
  - [ ] User documentation
  - [ ] System monitoring
  - [ ] Feedback collection

- **Week 6 Buffer Week 2**
