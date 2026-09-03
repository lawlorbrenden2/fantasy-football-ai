# 🏈 Fantasy Football AI (`fantasy-football-ai`)

An automated, data-driven decision engine designed to mathematically optimize a fantasy football season from the draft to the championship. 

Unlike standard "projected points" scripts, this project utilizes **Operations Research (Linear Programming)** to calculate real-time Value Over Replacement Player (VORP) during live drafts, and **Machine Learning** to generate weekly projections based on advanced NFL metrics. 

It is built as a highly decoupled, full-stack **Monorepo** to ensure the mathematical engine scales effortlessly into a modern web application.

---

## Core Features

* **Live Draft Optimizer:** Calculates dynamic VORP and baseline replacement scores to adapt to positional scarcity during snake drafts.
* **Weekly Automated GM:** Pulls live NFL data to recommend mathematically optimal waiver wire additions and starting lineups.
* **Trade Analyzer:** Simulates Rest-of-Season (ROS) roster outputs to evaluate the true numeric value of proposed trades.

---

## 🛠️ Tech Stack (To be completed later)

* **Core Engine:** Python, Pandas, PuLP (Linear Programming), Scikit-Learn/XGBoost
* **Backend API:** FastAPI
* **Frontend UI:** React, TypeScript, Vite
* **Architecture:** Clean Architecture Monorepo

---

## 📊 Data & Acknowledgments

* **nflverse:** NFL data and statistics accessed by this project are sourced from the [nflverse](https://github.com/nflverse). The nflverse is an open-source collection of repositories dedicated to data and analytics for the National Football League.
