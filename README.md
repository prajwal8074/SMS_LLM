# LLM accessibility for farmers

- Week 1 Ideation and Setup
  - [x] Discussion: [Minutes of Discussion](docs/Minutes-of-Discussion/README.md)
  - [x] Ideas:
    - ✅ [SMS LLM](docs/SMS_LLM.pdf)
    - ❌ [Marketplace MCP](docs/MarketplaceMCP.pdf)
  - [x] Initial Plan: [6 week plan](docs/6_week_plan.pdf)
  - [x] Research Results: [Indian Languages Translation Model](docs/Translate-100-languages) [Text To Speech Model](docs/Text-To-Speech-Unlimited) <p align="right">(**Aditya**)</p>
  - [x] Setup: [Call Interface Setup](Call-Interface/README.md) <p align="right">(**Prajwal**)</p>

- Week 2 Core Infrastructure
  - [x] Integrate API gateway with call interface, [Check Demo](Call-Interface) <p align="right">(**Prajwal**)</p>
  - [x] [AWS Setup](AWS) <p align="right">(**Shubham**)</p>
    - [x] Pre-trained LLM API(Gemini 2.5 Flash) and language translation
    - [x] Speech language detection for language translation model
    - [x] Basic speech-to-text and text to speech
    - [x] Integration of all models
  - [x] Reproducibility of AWS Setup using AWS CloudFormation <p align="right">(**Aditya**)</p>
  - [x] In Depth testing of the Lambda Function <p align="right">(**Akash**)</p>

- Week 3 MCP Server & Caching
  - [ ] Create a simple marketplace where session login is done using an active phone call and user id is phone number <p align="right">(**Shubham**)</p>
  - [ ] Set up CI/CD pipeline on github ensuring marketplace security <p align="right">(**Akash**)</p>
  - [ ] Simple caching system & FAQ database for common farming questions <p align="right">(**Aditya**)</p>
  - [ ] MCP Server for the marketplace and establish secure communication between AWS server and marketplace by salted hashing phone numbers <p align="right">(**Prajwal**)</p>

- Week 4 Buffer Week 1
  
- Week 5 Pilot Launch
  - [ ] Basic analytics tracking
  - [ ] User documentation
  - [ ] System monitoring
  - [ ] Feedback collection

- Week 6 Buffer Week 2
