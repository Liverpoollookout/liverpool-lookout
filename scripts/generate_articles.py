#!/usr/bin/env python3
"""
Liverpool Lookout — Automated Content Generator
Runs twice daily via GitHub Actions.
Generates 10 SEO-optimised articles per run using Claude API + free football data APIs.
Includes animated SVG illustrations for each article category.
"""
import os
import sys
import json
import time
import random
import re
import requests
from datetime import datetime, timezone, timedelta
import anthropic

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────
TEAM_ID = "133602"          # Liverpool FC on TheSportsDB
TEAM_NAME = "Liverpool FC"
MANAGER = "Arne Slot"
STADIUM = "Anfield"
SEASON = "2025-26"
CONTENT_DIR = "site/content/posts"
STATIC_DIR = "site/static"

KEY_PLAYERS = [
        "Mohamed Salah", "Virgil van Dijk", "Alisson Becker",
        "Dominik Szoboszlai", "Darwin Nunez", "Luis Diaz",
        "Ryan Gravenberch", "Alexis Mac Allister", "Cody Gakpo",
        "Joe Gomez", "Ibrahima Konate", "Trent Alexander-Arnold",
        "Harvey Elliott", "Jarell Quansah", "Caoimhin Kelleher"
]

ARTICLE_TYPES = [
        "match_preview", "match_report", "player_spotlight",
        "transfer_news", "tactical_analysis", "stats_analysis",
        "team_news", "historical", "opinion", "youth_academy"
]

CATEGORIES = {
        "match_preview":    "Match Previews",
        "match_report":     "Match Reports",
        "player_spotlight": "Player Analysis",
        "transfer_news":    "Transfer News",
        "tactical_analysis":"Tactical Analysis",
        "stats_analysis":   "Stats & Data",
        "team_news":        "Team News",
        "historical":       "History",
        "opinion":          "Opinion",
        "youth_academy":    "Academy"
}

# ──────────────────────────────────────────────
# ANIMATED SVG ILLUSTRATIONS
# Category-specific animated SVGs — no copyright issues
# ──────────────────────────────────────────────

def get_animated_svg(article_type: str, title: str = "") -> str:
        """Return an animated SVG string tailored to the article category."""
        svgs = {
            "match_preview": _svg_match_preview,
            "match_report":  _svg_match_report,
            "player_spotlight": _svg_player_spotlight,
            "transfer_news": _svg_transfer_news,
            "tactical_analysis": _svg_tactical_analysis,
            "stats_analysis": _svg_stats_analysis,
            "team_news": _svg_team_news,
            "historical": _svg_historical,
            "opinion": _svg_opinion,
            "youth_academy": _svg_academy,
        }
        fn = svgs.get(article_type, _svg_default)
        return fn()

def _svg_match_preview():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" class="article-svg" role="img" aria-label="Match Preview illustration">
          <defs>
              <linearGradient id="pitch" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color:#2d7a2d"/>
                          <stop offset="100%" style="stop-color:#1a5c1a"/>
                              </linearGradient>
                                </defs>
                                  <rect width="800" height="400" fill="url(#pitch)" rx="8"/>
                                    <!-- Pitch markings -->
                                      <rect x="60" y="40" width="680" height="320" fill="none" stroke="rgba(255,255,255,0.5)" stroke-width="2"/>
                                        <circle cx="400" cy="200" r="60" fill="none" stroke="rgba(255,255,255,0.5)" stroke-width="2"/>
                                          <line x1="400" y1="40" x2="400" y2="360" stroke="rgba(255,255,255,0.5)" stroke-width="2"/>
                                            <rect x="60" y="130" width="80" height="140" fill="none" stroke="rgba(255,255,255,0.5)" stroke-width="2"/>
                                              <rect x="660" y="130" width="80" height="140" fill="none" stroke="rgba(255,255,255,0.5)" stroke-width="2"/>
                                                <!-- Animated ball -->
                                                  <circle cx="200" cy="200" r="16" fill="white" stroke="#333" stroke-width="2">
                                                      <animate attributeName="cx" values="200;600;200" dur="3s" repeatCount="indefinite" calcMode="spline" keySplines="0.4 0 0.6 1; 0.4 0 0.6 1"/>
                                                          <animate attributeName="cy" values="200;120;200" dur="3s" repeatCount="indefinite" calcMode="spline" keySplines="0.4 0 0.6 1; 0.4 0 0.6 1"/>
                                                            </circle>
                                                              <!-- VS text -->
                                                                <text x="400" y="210" text-anchor="middle" font-family="Arial Black, sans-serif" font-size="28" font-weight="900" fill="white" opacity="0.9">MATCH PREVIEW</text>
                                                                  <!-- Countdown dots -->
                                                                    <circle cx="340" cy="240" r="6" fill="#C8102E"><animate attributeName="opacity" values="1;0.2;1" dur="1s" repeatCount="indefinite" begin="0s"/></circle>
                                                                      <circle cx="360" cy="240" r="6" fill="#C8102E"><animate attributeName="opacity" values="1;0.2;1" dur="1s" repeatCount="indefinite" begin="0.33s"/></circle>
                                                                        <circle cx="380" cy="240" r="6" fill="#C8102E"><animate attributeName="opacity" values="1;0.2;1" dur="1s" repeatCount="indefinite" begin="0.66s"/></circle>
                                                                          <circle cx="400" cy="240" r="6" fill="white"><animate attributeName="opacity" values="1;0.2;1" dur="1s" repeatCount="indefinite" begin="0s"/></circle>
                                                                            <circle cx="420" cy="240" r="6" fill="white"><animate attributeName="opacity" values="1;0.2;1" dur="1s" repeatCount="indefinite" begin="0.33s"/></circle>
                                                                              <circle cx="440" cy="240" r="6" fill="white"><animate attributeName="opacity" values="1;0.2;1" dur="1s" repeatCount="indefinite" begin="0.66s"/></circle>
                                                                                <circle cx="460" cy="240" r="6" fill="white"><animate attributeName="opacity" values="1;0.2;1" dur="1s" repeatCount="indefinite" begin="1s"/></circle>
                                                                                  <!-- Red badge -->
                                                                                    <rect x="290" y="50" width="220" height="50" rx="6" fill="#C8102E" opacity="0.9"/>
                                                                                      <text x="400" y="82" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" font-weight="700" fill="white">COMING UP</text>
                                                                                      </svg>'''

def _svg_match_report():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" class="article-svg" role="img" aria-label="Match Report illustration">
          <defs>
              <linearGradient id="bg-report" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#111111"/>
                          <stop offset="100%" style="stop-color:#C8102E"/>
                              </linearGradient>
                                </defs>
                                  <rect width="800" height="400" fill="url(#bg-report)" rx="8"/>
                                    <!-- Score display -->
                                      <rect x="200" y="80" width="400" height="180" rx="12" fill="rgba(0,0,0,0.5)"/>
                                        <text x="300" y="200" text-anchor="middle" font-family="Arial Black, sans-serif" font-size="72" font-weight="900" fill="white">LFC</text>
                                          <text x="400" y="200" text-anchor="middle" font-family="Arial Black, sans-serif" font-size="48" font-weight="900" fill="#C8102E">VS</text>
                                            <!-- Animated score counter -->
                                              <text x="500" y="200" text-anchor="middle" font-family="Arial Black, sans-serif" font-size="72" font-weight="900" fill="#aaa">OPP</text>
                                                <!-- Animated goal flash -->
                                                  <circle cx="400" cy="200" r="40" fill="#C8102E" opacity="0">
                                                      <animate attributeName="opacity" values="0;0.8;0" dur="2s" repeatCount="indefinite"/>
                                                          <animate attributeName="r" values="40;80;40" dur="2s" repeatCount="indefinite"/>
                                                            </circle>
                                                              <text x="400" y="320" text-anchor="middle" font-family="Arial, sans-serif" font-size="20" font-weight="700" fill="white" letter-spacing="4">MATCH REPORT</text>
                                                                <!-- Star particles -->
                                                                  <circle cx="150" cy="150" r="3" fill="#F6EB61"><animate attributeName="opacity" values="0;1;0" dur="1.5s" repeatCount="indefinite" begin="0s"/></circle>
                                                                    <circle cx="650" cy="150" r="3" fill="#F6EB61"><animate attributeName="opacity" values="0;1;0" dur="1.5s" repeatCount="indefinite" begin="0.5s"/></circle>
                                                                      <circle cx="150" cy="250" r="3" fill="#F6EB61"><animate attributeName="opacity" values="0;1;0" dur="1.5s" repeatCount="indefinite" begin="1s"/></circle>
                                                                        <circle cx="650" cy="250" r="3" fill="#F6EB61"><animate attributeName="opacity" values="0;1;0" dur="1.5s" repeatCount="indefinite" begin="0.75s"/></circle>
                                                                        </svg>'''

def _svg_player_spotlight():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" class="article-svg" role="img" aria-label="Player Analysis illustration">
          <defs>
              <radialGradient id="spotlight" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" style="stop-color:#C8102E;stop-opacity:0.3"/>
                          <stop offset="100%" style="stop-color:#111111;stop-opacity:1"/>
                              </radialGradient>
                                </defs>
                                  <rect width="800" height="400" fill="#111" rx="8"/>
                                    <ellipse cx="400" cy="200" rx="200" ry="180" fill="url(#spotlight)">
                                        <animate attributeName="rx" values="200;220;200" dur="2s" repeatCount="indefinite"/>
                                            <animate attributeName="ry" values="180;200;180" dur="2s" repeatCount="indefinite"/>
                                              </ellipse>
                                                <!-- Player silhouette -->
                                                  <g transform="translate(400, 200)">
                                                      <!-- Body -->
                                                          <ellipse cx="0" cy="-60" rx="22" ry="22" fill="#C8102E"/>
                                                              <rect x="-18" y="-38" width="36" height="50" rx="8" fill="#C8102E"/>
                                                                  <!-- Legs -->
                                                                      <rect x="-16" y="12" width="14" height="45" rx="6" fill="#C8102E">
                                                                            <animate attributeName="height" values="45;35;45" dur="0.8s" repeatCount="indefinite"/>
                                                                                </rect>
                                                                                    <rect x="2" y="12" width="14" height="35" rx="6" fill="#C8102E">
                                                                                          <animate attributeName="height" values="35;45;35" dur="0.8s" repeatCount="indefinite"/>
                                                                                              </rect>
                                                                                                  <!-- Arms -->
                                                                                                      <rect x="-32" y="-30" width="14" height="35" rx="6" fill="#C8102E" transform="rotate(-20, -32, -30)">
                                                                                                            <animateTransform attributeName="transform" type="rotate" values="-20,-32,-30;20,-32,-30;-20,-32,-30" dur="0.8s" repeatCount="indefinite"/>
                                                                                                                </rect>
                                                                                                                    <rect x="18" y="-30" width="14" height="35" rx="6" fill="#C8102E" transform="rotate(20, 18, -30)">
                                                                                                                          <animateTransform attributeName="transform" type="rotate" values="20,18,-30;-20,18,-30;20,18,-30" dur="0.8s" repeatCount="indefinite"/>
                                                                                                                              </rect>
                                                                                                                                  <!-- Ball at feet -->
                                                                                                                                      <circle cx="12" cy="65" r="10" fill="white" stroke="#333" stroke-width="1.5">
                                                                                                                                            <animate attributeName="cx" values="12;-12;12" dur="1.6s" repeatCount="indefinite"/>
                                                                                                                                                </circle>
                                                                                                                                                  </g>
                                                                                                                                                    <!-- Rating stars -->
                                                                                                                                                      <text x="400" y="330" text-anchor="middle" font-family="Arial, sans-serif" font-size="22" fill="#F6EB61">★ ★ ★ ★ ★</text>
                                                                                                                                                        <text x="400" y="360" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" font-weight="700" fill="white" letter-spacing="3">PLAYER SPOTLIGHT</text>
                                                                                                                                                        </svg>'''

def _svg_transfer_news():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" class="article-svg" role="img" aria-label="Transfer News illustration">
          <rect width="800" height="400" fill="#0a0a2e" rx="8"/>
            <!-- Money symbols raining -->
              <text x="80" y="100" font-family="Arial, sans-serif" font-size="30" fill="#4CAF50" opacity="0.8">
                  £<animate attributeName="y" values="100;350" dur="2s" repeatCount="indefinite"/>
                      <animate attributeName="opacity" values="0.8;0" dur="2s" repeatCount="indefinite"/>
                        </text>
                          <text x="180" y="50" font-family="Arial, sans-serif" font-size="24" fill="#4CAF50" opacity="0.7">
                              £<animate attributeName="y" values="50;350" dur="2.5s" repeatCount="indefinite" begin="0.5s"/>
                                  <animate attributeName="opacity" values="0.7;0" dur="2.5s" repeatCount="indefinite" begin="0.5s"/>
                                    </text>
                                      <text x="300" y="80" font-family="Arial, sans-serif" font-size="28" fill="#4CAF50" opacity="0.9">
                                          £<animate attributeName="y" values="80;350" dur="1.8s" repeatCount="indefinite" begin="1s"/>
                                              <animate attributeName="opacity" values="0.9;0" dur="1.8s" repeatCount="indefinite" begin="1s"/>
                                                </text>
                                                  <text x="450" y="60" font-family="Arial, sans-serif" font-size="32" fill="#4CAF50">
                                                      £<animate attributeName="y" values="60;350" dur="2.2s" repeatCount="indefinite" begin="0.3s"/>
                                                          <animate attributeName="opacity" values="1;0" dur="2.2s" repeatCount="indefinite" begin="0.3s"/>
                                                            </text>
                                                              <text x="580" y="90" font-family="Arial, sans-serif" font-size="26" fill="#4CAF50" opacity="0.8">
                                                                  £<animate attributeName="y" values="90;350" dur="2.8s" repeatCount="indefinite" begin="0.8s"/>
                                                                      <animate attributeName="opacity" values="0.8;0" dur="2.8s" repeatCount="indefinite" begin="0.8s"/>
                                                                        </text>
                                                                          <text x="700" y="70" font-family="Arial, sans-serif" font-size="22" fill="#4CAF50" opacity="0.7">
                                                                              £<animate attributeName="y" values="70;350" dur="2s" repeatCount="indefinite" begin="1.5s"/>
                                                                                  <animate attributeName="opacity" values="0.7;0" dur="2s" repeatCount="indefinite" begin="1.5s"/>
                                                                                    </text>
                                                                                      <!-- Arrow showing transfer -->
                                                                                        <path d="M 250 200 L 550 200" stroke="#C8102E" stroke-width="4" fill="none" stroke-dasharray="10,5">
                                                                                            <animate attributeName="stroke-dashoffset" values="0;-60" dur="1s" repeatCount="indefinite"/>
                                                                                              </path>
                                                                                                <polygon points="560,190 580,200 560,210" fill="#C8102E"/>
                                                                                                  <!-- Labels -->
                                                                                                    <rect x="100" y="165" width="130" height="70" rx="8" fill="rgba(200,16,46,0.8)"/>
                                                                                                      <text x="165" y="205" text-anchor="middle" font-family="Arial Black, sans-serif" font-size="16" font-weight="900" fill="white">SELLING</text>
                                                                                                        <text x="165" y="222" text-anchor="middle" font-family="Arial Black, sans-serif" font-size="12" fill="white">CLUB</text>
                                                                                                          <rect x="570" y="165" width="130" height="70" rx="8" fill="rgba(200,16,46,0.8)"/>
                                                                                                            <text x="635" y="205" text-anchor="middle" font-family="Arial Black, sans-serif" font-size="16" font-weight="900" fill="white">ANFIELD</text>
                                                                                                              <text x="635" y="222" text-anchor="middle" font-family="Arial Black, sans-serif" font-size="12" fill="white">BOUND?</text>
                                                                                                                <text x="400" y="320" text-anchor="middle" font-family="Arial, sans-serif" font-size="18" font-weight="700" fill="white" letter-spacing="4">TRANSFER NEWS</text>
                                                                                                                </svg>'''

def _svg_tactical_analysis():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" class="article-svg" role="img" aria-label="Tactical Analysis illustration">
          <rect width="800" height="400" fill="#1a1a2e" rx="8"/>
            <!-- Tactics board -->
              <rect x="80" y="40" width="640" height="320" rx="6" fill="#2d7a2d"/>
                <!-- Pitch lines -->
                  <rect x="100" y="60" width="600" height="280" fill="none" stroke="rgba(255,255,255,0.4)" stroke-width="1.5"/>
                    <circle cx="400" cy="200" r="50" fill="none" stroke="rgba(255,255,255,0.4)" stroke-width="1.5"/>
                      <line x1="400" y1="60" x2="400" y2="340" stroke="rgba(255,255,255,0.4)" stroke-width="1.5"/>
                        <!-- Animated formation dots - attacking team red -->
                          <circle cx="200" cy="200" r="12" fill="#C8102E"><animate attributeName="cy" values="200;195;200" dur="1.5s" repeatCount="indefinite"/></circle>
                            <circle cx="300" cy="130" r="12" fill="#C8102E"><animate attributeName="cy" values="130;125;130" dur="1.5s" repeatCount="indefinite" begin="0.1s"/></circle>
                              <circle cx="300" cy="200" r="12" fill="#C8102E"><animate attributeName="cy" values="200;195;200" dur="1.5s" repeatCount="indefinite" begin="0.2s"/></circle>
                                <circle cx="300" cy="270" r="12" fill="#C8102E"><animate attributeName="cy" values="270;265;270" dur="1.5s" repeatCount="indefinite" begin="0.3s"/></circle>
                                  <circle cx="370" cy="150" r="12" fill="#C8102E"><animate attributeName="cy" values="150;145;150" dur="1.5s" repeatCount="indefinite" begin="0.4s"/></circle>
                                    <circle cx="370" cy="250" r="12" fill="#C8102E"><animate attributeName="cy" values="250;245;250" dur="1.5s" repeatCount="indefinite" begin="0.5s"/></circle>
                                      <circle cx="430" cy="130" r="12" fill="#C8102E"><animate attributeName="cy" values="130;125;130" dur="1.5s" repeatCount="indefinite" begin="0.6s"/></circle>
                                        <circle cx="430" cy="200" r="12" fill="#C8102E"><animate attributeName="cy" values="200;195;200" dur="1.5s" repeatCount="indefinite" begin="0.7s"/></circle>
                                          <circle cx="430" cy="270" r="12" fill="#C8102E"><animate attributeName="cy" values="270;265;270" dur="1.5s" repeatCount="indefinite" begin="0.8s"/></circle>
                                            <circle cx="550" cy="160" r="12" fill="#C8102E"><animate attributeName="cy" values="160;155;160" dur="1.5s" repeatCount="indefinite" begin="0.9s"/></circle>
                                              <circle cx="550" cy="240" r="12" fill="#C8102E"><animate attributeName="cy" values="240;235;240" dur="1.5s" repeatCount="indefinite" begin="1s"/></circle>
                                                <!-- Tactical arrows -->
                                                  <path d="M 430 200 Q 490 170 550 200" stroke="yellow" stroke-width="2" fill="none" stroke-dasharray="6,4" opacity="0.8">
                                                      <animate attributeName="stroke-dashoffset" values="0;-40" dur="1s" repeatCount="indefinite"/>
                                                        </path>
                                                          <path d="M 370 150 Q 400 120 430 130" stroke="yellow" stroke-width="2" fill="none" stroke-dasharray="6,4" opacity="0.8">
                                                              <animate attributeName="stroke-dashoffset" values="0;-40" dur="1s" repeatCount="indefinite" begin="0.5s"/>
                                                                </path>
                                                                  <text x="400" y="385" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" font-weight="700" fill="white" letter-spacing="3">TACTICAL ANALYSIS</text>
                                                                  </svg>'''

def _svg_stats_analysis():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" class="article-svg" role="img" aria-label="Stats and Data illustration">
          <rect width="800" height="400" fill="#0d1117" rx="8"/>
            <!-- Animated bar chart -->
              <g transform="translate(80, 320)">
                  <!-- Bars growing up -->
                      <rect x="0" y="0" width="60" height="0" fill="#C8102E" transform="scale(1,-1)">
                            <animate attributeName="height" values="0;180;180" dur="1.5s" fill="freeze"/>
                                </rect>
                                    <rect x="80" y="0" width="60" height="0" fill="#C8102E" opacity="0.85" transform="scale(1,-1)">
                                          <animate attributeName="height" values="0;220;220" dur="1.5s" fill="freeze" begin="0.1s"/>
                                              </rect>
                                                  <rect x="160" y="0" width="60" height="0" fill="#C8102E" opacity="0.7" transform="scale(1,-1)">
                                                        <animate attributeName="height" values="0;150;150" dur="1.5s" fill="freeze" begin="0.2s"/>
                                                            </rect>
                                                                <rect x="240" y="0" width="60" height="0" fill="#C8102E" opacity="0.9" transform="scale(1,-1)">
                                                                      <animate attributeName="height" values="0;260;260" dur="1.5s" fill="freeze" begin="0.3s"/>
                                                                          </rect>
                                                                              <rect x="320" y="0" width="60" height="0" fill="#C8102E" opacity="0.75" transform="scale(1,-1)">
                                                                                    <animate attributeName="height" values="0;200;200" dur="1.5s" fill="freeze" begin="0.4s"/>
                                                                                        </rect>
                                                                                            <rect x="400" y="0" width="60" height="0" fill="#C8102E" opacity="0.8" transform="scale(1,-1)">
                                                                                                  <animate attributeName="height" values="0;240;240" dur="1.5s" fill="freeze" begin="0.5s"/>
                                                                                                      </rect>
                                                                                                          <rect x="480" y="0" width="60" height="0" fill="#4CAF50" opacity="0.8" transform="scale(1,-1)">
                                                                                                                <animate attributeName="height" values="0;190;190" dur="1.5s" fill="freeze" begin="0.6s"/>
                                                                                                                    </rect>
                                                                                                                        <rect x="560" y="0" width="60" height="0" fill="#4CAF50" opacity="0.9" transform="scale(1,-1)">
                                                                                                                              <animate attributeName="height" values="0;270;270" dur="1.5s" fill="freeze" begin="0.7s"/>
                                                                                                                                  </rect>
                                                                                                                                    </g>
                                                                                                                                      <!-- Baseline -->
                                                                                                                                        <line x1="70" y1="320" x2="740" y2="320" stroke="rgba(255,255,255,0.3)" stroke-width="1"/>
                                                                                                                                          <!-- Trend line animated -->
                                                                                                                                            <polyline points="110,280 190,240 270,265 350,200 430,220 510,240 590,195 670,160" fill="none" stroke="#F6EB61" stroke-width="2.5" stroke-dasharray="5,3" opacity="0.8">
                                                                                                                                                <animate attributeName="stroke-dashoffset" values="0;-40" dur="1s" repeatCount="indefinite"/>
                                                                                                                                                  </polyline>
                                                                                                                                                    <text x="400" y="370" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" font-weight="700" fill="white" letter-spacing="3">STATS &amp; DATA</text>
                                                                                                                                                    </svg>'''

def _svg_team_news():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" class="article-svg" role="img" aria-label="Team News illustration">
          <rect width="800" height="400" fill="#111827" rx="8"/>
            <!-- Newspaper / bulletin board feel -->
              <rect x="60" y="40" width="680" height="300" rx="6" fill="white" opacity="0.95"/>
                <!-- Breaking news banner -->
                  <rect x="60" y="40" width="680" height="55" rx="6" fill="#C8102E"/>
                    <text x="400" y="78" text-anchor="middle" font-family="Arial Black, sans-serif" font-size="22" font-weight="900" fill="white" letter-spacing="2">TEAM NEWS</text>
                      <!-- Animated live dot -->
                        <circle cx="120" cy="67" r="8" fill="#ff0">
                            <animate attributeName="opacity" values="1;0.2;1" dur="0.8s" repeatCount="indefinite"/>
                              </circle>
                                <text x="135" y="73" font-family="Arial, sans-serif" font-size="12" font-weight="700" fill="white">LIVE</text>
                                  <!-- News lines -->
                                    <rect x="90" y="115" width="400" height="14" rx="4" fill="#e0e0e0"/>
                                      <rect x="90" y="140" width="500" height="14" rx="4" fill="#e0e0e0"/>
                                        <rect x="90" y="165" width="350" height="14" rx="4" fill="#e0e0e0"/>
                                          <rect x="90" y="190" width="450" height="14" rx="4" fill="#e0e0e0"/>
                                            <rect x="90" y="215" width="300" height="14" rx="4" fill="#e0e0e0"/>
                                              <!-- Animated red highlight line -->
                                                <rect x="90" y="115" width="0" height="14" rx="4" fill="#C8102E" opacity="0.3">
                                                    <animate attributeName="width" values="0;400;0" dur="3s" repeatCount="indefinite"/>
                                                      </rect>
                                                        <!-- Player icons -->
                                                          <circle cx="620" cy="160" r="35" fill="#C8102E" opacity="0.2"/>
                                                            <ellipse cx="620" cy="145" rx="14" ry="14" fill="#C8102E" opacity="0.6"/>
                                                              <rect x="604" y="158" width="32" height="28" rx="8" fill="#C8102E" opacity="0.6"/>
                                                                <circle cx="660" cy="170" r="35" fill="#C8102E" opacity="0.15"/>
                                                                  <ellipse cx="660" cy="155" rx="14" ry="14" fill="#C8102E" opacity="0.4"/>
                                                                    <rect x="644" y="168" width="32" height="28" rx="8" fill="#C8102E" opacity="0.4"/>
                                                                    </svg>'''

def _svg_historical():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" class="article-svg" role="img" aria-label="Liverpool FC History illustration">
          <defs>
              <linearGradient id="hist-bg" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color:#1a0a00"/>
                          <stop offset="100%" style="stop-color:#3d1f00"/>
                              </linearGradient>
                                </defs>
                                  <rect width="800" height="400" fill="url(#hist-bg)" rx="8"/>
                                    <!-- Trophy silhouette -->
                                      <g transform="translate(400, 200)">
                                          <!-- Trophy cup -->
                                              <path d="M-40,-80 Q-50,-40 -30,0 L-20,30 L-5,30 L-5,50 L-25,50 L-25,65 L25,65 L25,50 L5,50 L5,30 L20,30 L30,0 Q50,-40 40,-80 Z" fill="#F6EB61" opacity="0.9">
                                                    <animate attributeName="opacity" values="0.9;1;0.9" dur="2s" repeatCount="indefinite"/>
                                                        </path>
                                                            <!-- Trophy shine -->
                                                                <path d="M-20,-60 Q-15,-40 -10,-20" stroke="white" stroke-width="3" fill="none" opacity="0.6">
                                                                      <animate attributeName="opacity" values="0.6;1;0.6" dur="1.5s" repeatCount="indefinite"/>
                                                                          </path>
                                                                              <!-- Handles -->
                                                                                  <path d="M-40,-50 Q-65,-50 -65,-20 Q-65,10 -30,0" stroke="#F6EB61" stroke-width="8" fill="none"/>
                                                                                      <path d="M40,-50 Q65,-50 65,-20 Q65,10 30,0" stroke="#F6EB61" stroke-width="8" fill="none"/>
                                                                                        </g>
                                                                                          <!-- Stars around trophy -->
                                                                                            <text x="200" y="150" font-family="Arial" font-size="24" fill="#F6EB61">★<animate attributeName="opacity" values="1;0.2;1" dur="2s" repeatCount="indefinite" begin="0s"/></text>
                                                                                              <text x="560" y="150" font-family="Arial" font-size="24" fill="#F6EB61">★<animate attributeName="opacity" values="1;0.2;1" dur="2s" repeatCount="indefinite" begin="0.5s"/></text>
                                                                                                <text x="160" y="260" font-family="Arial" font-size="20" fill="#F6EB61">★<animate attributeName="opacity" values="1;0.2;1" dur="2s" repeatCount="indefinite" begin="1s"/></text>
                                                                                                  <text x="600" y="260" font-family="Arial" font-size="20" fill="#F6EB61">★<animate attributeName="opacity" values="1;0.2;1" dur="2s" repeatCount="indefinite" begin="1.5s"/></text>
                                                                                                    <!-- On this day text -->
                                                                                                      <text x="400" y="340" text-anchor="middle" font-family="Georgia, serif" font-size="16" font-style="italic" fill="#F6EB61" opacity="0.9">On This Day in Liverpool FC History</text>
                                                                                                        <!-- Decorative border -->
                                                                                                          <rect x="30" y="20" width="740" height="360" rx="8" fill="none" stroke="#F6EB61" stroke-width="2" stroke-dasharray="10,6" opacity="0.4"/>
                                                                                                          </svg>'''

def _svg_opinion():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" class="article-svg" role="img" aria-label="Opinion article illustration">
          <rect width="800" height="400" fill="#1a1a2e" rx="8"/>
            <!-- Speech bubble left -->
              <rect x="60" y="80" width="280" height="160" rx="16" fill="#C8102E"/>
                <polygon points="100,240 80,280 140,240" fill="#C8102E"/>
                  <text x="200" y="150" text-anchor="middle" font-family="Georgia, serif" font-size="48" fill="white" opacity="0.9">"</text>
                    <text x="200" y="195" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" fill="white">My View...</text>
                      <!-- Speech bubble right -->
                        <rect x="460" y="120" width="280" height="160" rx="16" fill="#444"/>
                          <polygon points="700,280 720,320 660,280" fill="#444"/>
                            <text x="600" y="190" text-anchor="middle" font-family="Georgia, serif" font-size="48" fill="white" opacity="0.6">"</text>
                              <text x="600" y="235" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" fill="#ccc">Counter point...</text>
                                <!-- Animated VS indicator -->
                                  <text x="400" y="215" text-anchor="middle" font-family="Arial Black, sans-serif" font-size="32" font-weight="900" fill="white">VS</text>
                                    <circle cx="400" cy="202" r="30" fill="none" stroke="white" stroke-width="2">
                                        <animate attributeName="r" values="30;35;30" dur="1.5s" repeatCount="indefinite"/>
                                            <animate attributeName="opacity" values="1;0.5;1" dur="1.5s" repeatCount="indefinite"/>
                                              </circle>
                                                <text x="400" y="360" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" font-weight="700" fill="white" letter-spacing="4">OPINION</text>
                                                </svg>'''

def _svg_academy():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" class="article-svg" role="img" aria-label="Academy Youth Football illustration">
          <defs>
              <linearGradient id="academy-bg" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#0d2137"/>
                          <stop offset="100%" style="stop-color:#1a3a5c"/>
                              </linearGradient>
                                </defs>
                                  <rect width="800" height="400" fill="url(#academy-bg)" rx="8"/>
                                    <!-- Stars of the future -->
                                      <text x="400" y="60" text-anchor="middle" font-family="Arial Black, sans-serif" font-size="14" font-weight="700" fill="#F6EB61" letter-spacing="4">STARS OF THE FUTURE</text>
                                        <!-- Small player silhouettes growing -->
                                          <g transform="translate(200,300)">
                                              <ellipse cx="0" cy="-30" rx="12" ry="12" fill="#C8102E" opacity="0.5"/>
                                                  <rect x="-8" y="-18" width="16" height="25" rx="5" fill="#C8102E" opacity="0.5"/>
                                                    </g>
                                                      <g transform="translate(300,280)">
                                                          <ellipse cx="0" cy="-35" rx="14" ry="14" fill="#C8102E" opacity="0.7"/>
                                                              <rect x="-10" y="-21" width="20" height="30" rx="5" fill="#C8102E" opacity="0.7"/>
                                                                </g>
                                                                  <g transform="translate(400,260)">
                                                                      <ellipse cx="0" cy="-40" rx="16" ry="16" fill="#C8102E" opacity="0.85"/>
                                                                          <rect x="-12" y="-24" width="24" height="35" rx="6" fill="#C8102E" opacity="0.85"/>
                                                                              <!-- Star on biggest player -->
                                                                                  <text x="0" y="-60" text-anchor="middle" font-family="Arial" font-size="18" fill="#F6EB61">
                                                                                        ★<animate attributeName="opacity" values="1;0.3;1" dur="1.2s" repeatCount="indefinite"/>
                                                                                            </text>
                                                                                              </g>
                                                                                                <g transform="translate(500,275)">
                                                                                                    <ellipse cx="0" cy="-35" rx="14" ry="14" fill="#C8102E" opacity="0.65"/>
                                                                                                        <rect x="-10" y="-21" width="20" height="30" rx="5" fill="#C8102E" opacity="0.65"/>
                                                                                                          </g>
                                                                                                            <g transform="translate(600,295)">
                                                                                                                <ellipse cx="0" cy="-28" rx="12" ry="12" fill="#C8102E" opacity="0.45"/>
                                                                                                                    <rect x="-8" y="-16" width="16" height="22" rx="5" fill="#C8102E" opacity="0.45"/>
                                                                                                                      </g>
                                                                                                                        <!-- Growth arrow -->
                                                                                                                          <path d="M 150 310 Q 280 200 400 160 Q 520 120 650 100" stroke="#F6EB61" stroke-width="3" fill="none" stroke-dasharray="8,4" opacity="0.6">
                                                                                                                              <animate attributeName="stroke-dashoffset" values="0;-48" dur="1.5s" repeatCount="indefinite"/>
                                                                                                                                </path>
                                                                                                                                  <!-- Path to first team text -->
                                                                                                                                    <text x="400" y="360" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" font-weight="700" fill="white" letter-spacing="3">ACADEMY &amp; YOUTH</text>
                                                                                                                                    </svg>'''

def _svg_default():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" class="article-svg" role="img" aria-label="Liverpool FC article illustration">
          <defs>
              <linearGradient id="default-bg" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#C8102E"/>
                          <stop offset="100%" style="stop-color:#8b0c20"/>
                              </linearGradient>
                                </defs>
                                  <rect width="800" height="400" fill="url(#default-bg)" rx="8"/>
                                    <!-- Liverpool FC crest shape (simplified) -->
                                      <g transform="translate(400,190)">
                                          <!-- Shield outline -->
                                              <path d="M0,-110 L70,-90 L90,-30 L70,50 L0,90 L-70,50 L-90,-30 L-70,-90 Z" fill="none" stroke="white" stroke-width="3" opacity="0.8">
                                                    <animate attributeName="opacity" values="0.8;1;0.8" dur="2s" repeatCount="indefinite"/>
                                                        </path>
                                                            <!-- LFC text -->
                                                                <text x="0" y="15" text-anchor="middle" font-family="Arial Black, sans-serif" font-size="42" font-weight="900" fill="white" opacity="0.95">LFC</text>
                                                                    <!-- Season badge -->
                                                                        <text x="0" y="50" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" fill="white" opacity="0.8">2025-26</text>
                                                                          </g>
                                                                            <!-- Animated pulse ring -->
                                                                              <circle cx="400" cy="190" r="120" fill="none" stroke="rgba(255,255,255,0.3)" stroke-width="2">
                                                                                  <animate attributeName="r" values="120;140;120" dur="2s" repeatCount="indefinite"/>
                                                                                      <animate attributeName="opacity" values="0.3;0;0.3" dur="2s" repeatCount="indefinite"/>
                                                                                        </circle>
                                                                                          <text x="400" y="360" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" font-weight="700" fill="white" opacity="0.9" letter-spacing="4">LIVERPOOL LOOKOUT</text>
                                                                                          </svg>'''

# ──────────────────────────────────────────────
# DATA FETCHING
# ──────────────────────────────────────────────
def fetch_json(url, fallback=None):
        try:
                    r = requests.get(url, timeout=12, headers={"User-Agent": "LiverpoolLookout/1.0"})
                    r.raise_for_status()
                    return r.json()
except Exception as e:
        print(f"  Warning: Fetch failed {url}: {e}")
        return fallback or {}

def fetch_fixtures():
        data = fetch_json(f"https://www.thesportsdb.com/api/v1/json/3/eventsnext.php?id={TEAM_ID}")
        return data.get("events", [])[:5]

def fetch_last_results():
        data = fetch_json(f"https://www.thesportsdb.com/api/v1/json/3/eventslast.php?id={TEAM_ID}")
        return data.get("results", [])[:5]

def fetch_squad():
        data = fetch_json(f"https://www.thesportsdb.com/api/v1/json/3/lookup_all_players.php?id={TEAM_ID}")
        players = data.get("player", []) or []
        return [p for p in players if p.get("strStatus") == "Active"]

def fetch_lfc_news_rss():
        try:
                    r = requests.get(
                                    "https://feeds.bbci.co.uk/sport/football/teams/liverpool/rss.xml",
                                    timeout=12,
                                    headers={"User-Agent": "LiverpoolLookout/1.0"}
                    )
                    headlines = re.findall(r"<title><!\[CDATA\[(.*?)\]\]></title>", r.text)
                    return [h for h in headlines if "Liverpool" in h or "LFC" in h][:10]
                except:
        return []

# ──────────────────────────────────────────────
# SLUG / FILE HELPERS
# ──────────────────────────────────────────────
def slugify(text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"[\s_]+", "-", text)
        text = re.sub(r"-+", "-", text)
        return text[:80].strip("-")

def get_existing_slugs() -> set:
        if not os.path.exists(CONTENT_DIR):
                    return set()
                return {f.replace(".md", "") for f in os.listdir(CONTENT_DIR) if f.endswith(".md")}

def date_slug_prefix() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

# ──────────────────────────────────────────────
# ARTICLE PROMPTS
# ──────────────────────────────────────────────
BASE_INSTRUCTIONS = """
You are a professional football journalist specialising in Liverpool FC.
Write authoritative, engaging, original content for LiverpoolLookout.com.
Always use UK English spelling (colour, defence, favour, etc.).
Never make up specific scorelines, quotes from named people, or confirmed transfer fees unless given in context.
Use "according to reports", "sources suggest" for rumours.
"""

PROMPTS = {
        "match_preview": lambda ctx: f"""{BASE_INSTRUCTIONS}
        Write a Liverpool FC MATCH PREVIEW article (650-850 words).
        Context data: {json.dumps(ctx, indent=2)}
        Cover: expected lineups, key battles, tactical approach, recent form, prediction.
        Make the headline compelling and include both team names.
        End with a confident prediction section.
        Return ONLY valid JSON: {{"title": "...", "meta_description": "...(max 155 chars)", "content": "...markdown...", "tags": ["tag1","tag2","tag3","tag4","tag5"], "category": "Match Previews"}}
        """,
        "match_report": lambda ctx: f"""{BASE_INSTRUCTIONS}
        Write a Liverpool FC MATCH REPORT article (750-950 words).
        Context data: {json.dumps(ctx, indent=2)}
        Cover: match narrative, key moments, goals, standout performers, manager reaction tone.
        Include a "## Player Ratings" section (1-10) at the end.
        Return ONLY valid JSON: {{"title": "...", "meta_description": "...(max 155 chars)", "content": "...markdown...", "tags": ["tag1","tag2","tag3","tag4","tag5"], "category": "Match Reports"}}
        """,
        "player_spotlight": lambda ctx: f"""{BASE_INSTRUCTIONS}
        Write a Liverpool FC PLAYER SPOTLIGHT article (650-850 words).
        Focus player: {ctx.get("player", "Mohamed Salah")}
        Context data: {json.dumps(ctx, indent=2)}
        Cover: recent form, role in the team, strengths, areas to improve, statistics context, fan verdict.
        Return ONLY valid JSON: {{"title": "...", "meta_description": "...(max 155 chars)", "content": "...markdown...", "tags": ["tag1","tag2","tag3","tag4","tag5"], "category": "Player Analysis"}}
        """,
        "transfer_news": lambda ctx: f"""{BASE_INSTRUCTIONS}
        Write a Liverpool FC TRANSFER NEWS article (550-750 words).
        Context data: {json.dumps(ctx, indent=2)}
        Cover: potential targets, reported links, likely fees (use "reported" language), how they would fit at Anfield.
        Be responsible - clearly label rumours vs confirmed news.
        Return ONLY valid JSON: {{"title": "...", "meta_description": "...(max 155 chars)", "content": "...markdown...", "tags": ["tag1","tag2","tag3","tag4","tag5"], "category": "Transfer News"}}
        """,
        "tactical_analysis": lambda ctx: f"""{BASE_INSTRUCTIONS}
        Write a Liverpool FC TACTICAL ANALYSIS article (750-950 words).
        Context data: {json.dumps(ctx, indent=2)}
        Cover: Arne Slot's system (4-2-3-1 / 4-3-3 hybrid), pressing triggers, build-up patterns, set-piece routines.
        Use proper tactical terminology. Include a "## Key Tactical Principles" section.
        Return ONLY valid JSON: {{"title": "...", "meta_description": "...(max 155 chars)", "content": "...markdown...", "tags": ["tag1","tag2","tag3","tag4","tag5"], "category": "Tactical Analysis"}}
        """,
        "stats_analysis": lambda ctx: f"""{BASE_INSTRUCTIONS}
        Write a Liverpool FC STATS AND DATA article (650-850 words).
        Context data: {json.dumps(ctx, indent=2)}
        Focus on one statistical theme. Use plausible, contextually appropriate statistics.
        Clearly present stats in markdown tables where appropriate.
        Return ONLY valid JSON: {{"title": "...", "meta_description": "...(max 155 chars)", "content": "...markdown...", "tags": ["tag1","tag2","tag3","tag4","tag5"], "category": "Stats & Data"}}
        """,
        "team_news": lambda ctx: f"""{BASE_INSTRUCTIONS}
        Write a Liverpool FC TEAM NEWS article (450-650 words).
        Context data: {json.dumps(ctx, indent=2)}
        Cover: injury updates, returns from fitness, suspensions, squad rotation plans.
        Return ONLY valid JSON: {{"title": "...", "meta_description": "...(max 155 chars)", "content": "...markdown...", "tags": ["tag1","tag2","tag3","tag4","tag5"], "category": "Team News"}}
        """,
        "historical": lambda ctx: f"""{BASE_INSTRUCTIONS}
        Write an "On This Day" or HISTORICAL RETROSPECTIVE article about Liverpool FC (750-950 words).
        Context data: {json.dumps(ctx, indent=2)}
        Choose a famous match, signing, trophy, or moment in Liverpool history. Rich storytelling approach.
        Return ONLY valid JSON: {{"title": "...", "meta_description": "...(max 155 chars)", "content": "...markdown...", "tags": ["tag1","tag2","tag3","tag4","tag5"], "category": "History"}}
        """,
        "opinion": lambda ctx: f"""{BASE_INSTRUCTIONS}
        Write an OPINION COLUMN article about Liverpool FC (600-800 words).
        Context data: {json.dumps(ctx, indent=2)}
        Take a clear, well-argued stance on a topical Liverpool FC debate.
        Structure: hook intro, argument, counter-argument, your verdict.
        Return ONLY valid JSON: {{"title": "...", "meta_description": "...(max 155 chars)", "content": "...markdown...", "tags": ["tag1","tag2","tag3","tag4","tag5"], "category": "Opinion"}}
        """,
        "youth_academy": lambda ctx: f"""{BASE_INSTRUCTIONS}
        Write a Liverpool FC ACADEMY AND YOUTH article (550-750 words).
        Context data: {json.dumps(ctx, indent=2)}
        Cover rising talent from Liverpool's academy, U21s, or loan players.
        Return ONLY valid JSON: {{"title": "...", "meta_description": "...(max 155 chars)", "content": "...markdown...", "tags": ["tag1","tag2","tag3","tag4","tag5"], "category": "Academy"}}
        """,
}

# ──────────────────────────────────────────────
# GENERATION
# ──────────────────────────────────────────────
def generate_article(client: anthropic.Anthropic, article_type: str, context: dict) -> dict:
        prompt_fn = PROMPTS.get(article_type, PROMPTS["team_news"])
    prompt = prompt_fn(context)
    message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
    )
    raw = message.content[0].text.strip()
    raw = re.sub(r"^```json\s*", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"\s*```$", "", raw, flags=re.MULTILINE)
    raw = raw.strip()
    return json.loads(raw)


def save_article(article: dict, article_type: str, existing_slugs: set) -> str | None:
        now = datetime.now(timezone.utc)
    iso_date = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    prefix = now.strftime("%Y-%m-%d")
    title = article.get("title", "Liverpool FC Update")
    slug_base = slugify(title)
    slug = f"{prefix}-{slug_base}"

    if slug in existing_slugs:
                slug = f"{slug}-{random.randint(100, 999)}"
            existing_slugs.add(slug)
    filename = f"{slug}.md"
    filepath = os.path.join(CONTENT_DIR, filename)

    tags = article.get("tags", ["Liverpool FC", "LFC", "Premier League"])
    category = article.get("category", "News")
    meta_desc = article.get("meta_description", "")[:155]
    content_body = article.get("content", "")

    # Get animated SVG for this article type
    svg_content = get_animated_svg(article_type, title)
    # Escape for YAML frontmatter (store as param)
    svg_escaped = svg_content.replace('"', "'")

    tags_yaml = "\n".join(f'  - "{t}"' for t in tags)
    frontmatter = f"""---
    title: "{title.replace('"', "'")}"
date: {iso_date}
description: "{meta_desc.replace('"', "'")}"
tags:
{tags_yaml}
categories:
  - "{category}"
article_type: "{article_type}"
draft: false
sitemap:
  changefreq: daily
  priority: 0.8
---
"""
    # Prepend the animated SVG to the article content
        full_content = frontmatter + f'\n<div class="article-illustration">\n{svg_content}\n</div>\n\n' + content_body

            os.makedirs(CONTENT_DIR, exist_ok=True)
                with open(filepath, "w", encoding="utf-8") as f:
                        f.write(full_content)
                            return filename

                            # ──────────────────────────────────────────────
                            # ARTICLE PLAN
                            # ──────────────────────────────────────────────
                            def build_article_plan(fixtures, results, headlines) -> list:
                                """Build 10 varied articles for this run."""
                                    base = {
                                            "team": TEAM_NAME,
                                                    "manager": MANAGER,
                                                            "stadium": STADIUM,
                                                                    "season": SEASON,
                                                                            "key_players": KEY_PLAYERS,
                                                                                    "recent_headlines": headlines[:5],
                                                                                            "today": datetime.now(timezone.utc).strftime("%d %B %Y"),
                                                                                                    "day_of_week": datetime.now(timezone.utc).strftime("%A"),
                                                                                                        }
                                                                                                            next_match = fixtures[0] if fixtures else {}
                                                                                                                last_result = results[0] if results else {}
                                                                                                                    recent_results = results[:3] if results else []
                                                                                                                        players_pool = KEY_PLAYERS.copy()
                                                                                                                            random.shuffle(players_pool)
                                                                                                                            
                                                                                                                                plan = [
                                                                                                                                        ("match_preview", {
                                                                                                                                                    **base,
                                                                                                                                                                "next_match": next_match,
                                                                                                                                                                            "recent_form": recent_results,
                                                                                                                                                                                        "focus": "detailed match preview with lineup predictions"
        }),
                ("player_spotlight", {
                            **base,
                                        "player": players_pool[0],
                                                    "recent_results": recent_results,
                                                                "focus": "current season form and contribution"
        }),
                ("transfer_news", {
                            **base,
                                        "focus": "summer transfer targets and potential incomings",
                                                    "rumour_tier": "Tier 2-3 links from European clubs"
        }),
                ("tactical_analysis", {
                            **base,
                                        "recent_results": recent_results,
                                                    "focus": "pressing system, high line, and build-up play under Arne Slot"
        }),
                ("stats_analysis", {
                            **base,
                                        "focus": "Premier League attacking statistics comparison - top 6 clubs",
                                                    "metric_theme": random.choice([
                                                                    "xG and xGA", "pressing intensity", "goals from set pieces",
                                                                                    "clean sheet ratio", "shots on target percentage"
            ])
                    }),
                            ("team_news", {
                                        **base,
                                                    "upcoming": next_match,
                                                                "focus": "injury and fitness update ahead of next fixture"
        }),
                ("historical", {
                            **base,
                                        "focus": "famous Liverpool FC moment, signing or match from club history",
                                                    "era_hint": random.choice([
                                                                    "Shankly era (1959-74)", "Paisley golden age (1974-83)",
                                                                                    "Dalglish era", "Gerrard years (2000s)", "Klopp era (2015-2024)"
            ])
                    }),
                            ("player_spotlight", {
                                        **base,
                                                    "player": players_pool[1],
                                                                "focus": "xG contribution, progressive carries, and impact on pressing"
        }),
                ("opinion", {
                            **base,
                                        "last_result": last_result,
                                                    "topic": random.choice([
                                                                    "Is Slot's Liverpool better than Klopp's?",
                                                                                    "The title race - can Liverpool hold on?",
                                                                                                    "Why Liverpool must prioritise the summer transfer window",
                                                                                                                    "The case for promoting an academy player to first-team",
                                                                                                                                    "Liverpool's injury crisis: is the fixture calendar too demanding?"
            ])
                    }),
                            ("youth_academy", {
                                        **base,
                                                    "focus": "Liverpool Academy graduates and current U21 standouts",
                                                                "player_hint": random.choice([
                                                                                "Ben Doak", "Bobby Clark", "Luke Chambers",
                                                                                                "James McConnell", "Trey Nyoni"
            ])
                    }),
                        ]
                            random.shuffle(plan)
                                return plan

                                # ──────────────────────────────────────────────
                                # MAIN
                                # ──────────────────────────────────────────────
                                def main():
                                    api_key = os.environ.get("ANTHROPIC_API_KEY")
                                        if not api_key:
                                                print("ERROR: ANTHROPIC_API_KEY environment variable is not set.")
                                                        sys.exit(1)

                                                            client = anthropic.Anthropic(api_key=api_key)

                                                                print("Fetching Liverpool FC data from TheSportsDB...")
                                                                    fixtures = fetch_fixtures()
                                                                        results = fetch_last_results()
                                                                            headlines = fetch_lfc_news_rss()
                                                                                print(f"  {len(fixtures)} upcoming fixtures, {len(results)} recent results, {len(headlines)} headlines")

                                                                                    plan = build_article_plan(fixtures, results, headlines)
                                                                                        existing_slugs = get_existing_slugs()
                                                                                            print(f"  {len(existing_slugs)} existing articles found\n")

                                                                                                generated, errors = 0, 0
                                                                                                    for i, (article_type, context) in enumerate(plan, 1):
                                                                                                            print(f"[{i}/{len(plan)}] Generating {article_type}...")
                                                                                                                    try:
                                                                                                                                article = generate_article(client, article_type, context)
                                                                                                                                            filename = save_article(article, article_type, existing_slugs)
                                                                                                                                                        print(f"  Saved: {filename}")
                                                                                                                                                                    generated += 1
                                                                                                                                                                                time.sleep(1.5)
                                                                                                                                                                                        except json.JSONDecodeError as e:
                                                                                                                                                                                                    print(f"  JSON parse error: {e}")
                                                                                                                                                                                                                errors += 1
                                                                                                                                                                                                                        except Exception as e:
                                                                                                                                                                                                                                    print(f"  Error: {e}")
                                                                                                                                                                                                                                                errors += 1
                                                                                                                                                                                                                                                
                                                                                                                                                                                                                                                    print(f"\n{'='*50}")
                                                                                                                                                                                                                                                        print(f"Generated: {generated} | Errors: {errors}")
                                                                                                                                                                                                                                                            print(f"{'='*50}")
                                                                                                                                                                                                                                                                if generated == 0:
                                                                                                                                                                                                                                                                        sys.exit(1)
                                                                                                                                                                                                                                                                        
                                                                                                                                                                                                                                                                        
                                                                                                                                                                                                                                                                        if __name__ == "__main__":
                                                                                                                                                                                                                                                                            main()
