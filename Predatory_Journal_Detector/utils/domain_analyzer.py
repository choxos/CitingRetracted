#!/usr/bin/env python3
"""
Domain Analysis Utilities
Analyze domain characteristics for predatory journal detection
"""

import whois
import socket
import ssl
import dns.resolver
from urllib.parse import urlparse
from datetime import datetime, timedelta
import re
from typing import Dict, Optional, List
import requests
import logging

class DomainAnalyzer:
    """Analyze domain characteristics to assess legitimacy"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Suspicious TLDs often used by predatory publishers
        self.suspicious_tlds = {
            '.tk', '.ml', '.ga', '.cf', '.gq', '.pw', '.top', 
            '.club', '.work', '.click', '.link', '.download'
        }
        
        # Legitimate academic domains
        self.academic_domains = {
            '.edu', '.ac.uk', '.edu.au', '.ac.jp', '.ac.in',
            '.university', '.college', '.institute'
        }
        
        # Known legitimate publishers
        self.legitimate_publishers = {
            'nature.com', 'sciencemag.org', 'cell.com', 'nejm.org',
            'bmj.com', 'thelancet.com', 'springer.com', 'elsevier.com',
            'wiley.com', 'tandfonline.com', 'sagepub.com', 'oup.com',
            'cambridge.org', 'plos.org', 'frontiersin.org', 'mdpi.com',
            'biomedcentral.com', 'hindawi.com', 'ieee.org', 'acm.org'
        }
    
    def analyze_domain(self, domain: str) -> Dict:
        """
        Comprehensive domain analysis
        
        Args:
            domain: Domain name to analyze
            
        Returns:
            Dictionary with domain analysis results
        """
        analysis = {
            'domain': domain,
            'is_suspicious': False,
            'risk_score': 0,
            'whois_info': {},
            'dns_info': {},
            'ssl_info': {},
            'legitimacy_indicators': [],
            'warning_flags': [],
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        try:
            # WHOIS analysis
            whois_data = self.analyze_whois(domain)
            analysis['whois_info'] = whois_data
            
            # DNS analysis
            dns_data = self.analyze_dns(domain)
            analysis['dns_info'] = dns_data
            
            # SSL certificate analysis
            ssl_data = self.analyze_ssl(domain)
            analysis['ssl_info'] = ssl_data
            
            # Domain characteristics analysis
            domain_chars = self.analyze_domain_characteristics(domain)
            analysis.update(domain_chars)
            
            # Calculate overall risk score
            analysis['risk_score'] = self.calculate_domain_risk_score(analysis)
            analysis['is_suspicious'] = analysis['risk_score'] > 50
            
        except Exception as e:
            self.logger.error(f"Domain analysis failed for {domain}: {e}")
            analysis['error'] = str(e)
        
        return analysis
    
    def analyze_whois(self, domain: str) -> Dict:
        """Analyze WHOIS information"""
        whois_info = {
            'registrar': None,
            'creation_date': None,
            'expiration_date': None,
            'updated_date': None,
            'registrant_country': None,
            'registrant_org': None,
            'domain_age_days': None,
            'privacy_protected': False,
            'suspicious_registrar': False
        }
        
        try:
            w = whois.whois(domain)
            
            # Basic information
            whois_info['registrar'] = w.registrar
            whois_info['creation_date'] = w.creation_date
            whois_info['expiration_date'] = w.expiration_date
            whois_info['updated_date'] = w.updated_date
            
            # Handle dates (can be list or single value)
            creation_date = w.creation_date
            if isinstance(creation_date, list):
                creation_date = creation_date[0]
            
            if creation_date:
                whois_info['creation_date'] = creation_date.isoformat() if hasattr(creation_date, 'isoformat') else str(creation_date)
                domain_age = datetime.now() - creation_date
                whois_info['domain_age_days'] = domain_age.days
            
            # Registrant information
            if hasattr(w, 'country'):
                whois_info['registrant_country'] = w.country
            if hasattr(w, 'org'):
                whois_info['registrant_org'] = w.org
            
            # Privacy protection check
            privacy_indicators = ['privacy', 'protection', 'whoisguard', 'proxy']
            registrar_lower = (w.registrar or '').lower()
            whois_info['privacy_protected'] = any(indicator in registrar_lower for indicator in privacy_indicators)
            
            # Suspicious registrar check
            suspicious_registrars = ['namecheap', 'godaddy privacy', 'domains by proxy', 'whoisguard']
            whois_info['suspicious_registrar'] = any(susp in registrar_lower for susp in suspicious_registrars)
            
        except Exception as e:
            whois_info['error'] = str(e)
            self.logger.warning(f"WHOIS lookup failed for {domain}: {e}")
        
        return whois_info
    
    def analyze_dns(self, domain: str) -> Dict:
        """Analyze DNS configuration"""
        dns_info = {
            'mx_records': [],
            'a_records': [],
            'nameservers': [],
            'has_spf': False,
            'has_dmarc': False,
            'suspicious_mx': False
        }
        
        try:
            # MX records
            try:
                mx_records = dns.resolver.resolve(domain, 'MX')
                dns_info['mx_records'] = [str(mx) for mx in mx_records]
            except:
                pass
            
            # A records
            try:
                a_records = dns.resolver.resolve(domain, 'A')
                dns_info['a_records'] = [str(a) for a in a_records]
            except:
                pass
            
            # Nameservers
            try:
                ns_records = dns.resolver.resolve(domain, 'NS')
                dns_info['nameservers'] = [str(ns) for ns in ns_records]
            except:
                pass
            
            # SPF record check
            try:
                txt_records = dns.resolver.resolve(domain, 'TXT')
                for record in txt_records:
                    if 'v=spf1' in str(record):
                        dns_info['has_spf'] = True
                        break
            except:
                pass
            
            # DMARC check
            try:
                dmarc_domain = f'_dmarc.{domain}'
                dmarc_records = dns.resolver.resolve(dmarc_domain, 'TXT')
                for record in dmarc_records:
                    if 'v=DMARC1' in str(record):
                        dns_info['has_dmarc'] = True
                        break
            except:
                pass
            
            # Check for suspicious MX records
            suspicious_mx_providers = ['guerrillamail', 'tempmail', '10minutemail']
            mx_text = ' '.join(dns_info['mx_records']).lower()
            dns_info['suspicious_mx'] = any(susp in mx_text for susp in suspicious_mx_providers)
            
        except Exception as e:
            dns_info['error'] = str(e)
            self.logger.warning(f"DNS analysis failed for {domain}: {e}")
        
        return dns_info
    
    def analyze_ssl(self, domain: str) -> Dict:
        """Analyze SSL certificate"""
        ssl_info = {
            'has_ssl': False,
            'issuer': None,
            'subject': None,
            'expires': None,
            'self_signed': False,
            'valid': False,
            'days_until_expiry': None
        }
        
        try:
            # Create SSL context
            context = ssl.create_default_context()
            
            # Connect and get certificate
            with socket.create_connection((domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as secure_sock:
                    cert = secure_sock.getpeercert()
                    
                    ssl_info['has_ssl'] = True
                    ssl_info['valid'] = True
                    
                    # Certificate details
                    ssl_info['issuer'] = dict(x[0] for x in cert.get('issuer', []))
                    ssl_info['subject'] = dict(x[0] for x in cert.get('subject', []))
                    
                    # Expiration date
                    expires_str = cert.get('notAfter')
                    if expires_str:
                        expires = datetime.strptime(expires_str, '%b %d %H:%M:%S %Y %Z')
                        ssl_info['expires'] = expires.isoformat()
                        days_until_expiry = (expires - datetime.now()).days
                        ssl_info['days_until_expiry'] = days_until_expiry
                    
                    # Check if self-signed
                    issuer = ssl_info['issuer']
                    subject = ssl_info['subject']
                    if issuer and subject:
                        ssl_info['self_signed'] = (
                            issuer.get('commonName') == subject.get('commonName') and
                            issuer.get('organizationName') == subject.get('organizationName')
                        )
        
        except Exception as e:
            ssl_info['error'] = str(e)
            ssl_info['has_ssl'] = False
        
        return ssl_info
    
    def analyze_domain_characteristics(self, domain: str) -> Dict:
        """Analyze domain name characteristics"""
        analysis = {
            'tld': '',
            'domain_length': 0,
            'has_numbers': False,
            'has_hyphens': False,
            'suspicious_tld': False,
            'academic_domain': False,
            'legitimate_publisher': False,
            'typosquatting_risk': False,
            'legitimacy_indicators': [],
            'warning_flags': []
        }
        
        # Extract TLD
        parts = domain.split('.')
        if len(parts) >= 2:
            analysis['tld'] = '.' + '.'.join(parts[-2:]) if parts[-1] in ['uk', 'au', 'in', 'jp'] else '.' + parts[-1]
        
        # Basic characteristics
        analysis['domain_length'] = len(domain)
        analysis['has_numbers'] = bool(re.search(r'\d', domain))
        analysis['has_hyphens'] = '-' in domain
        
        # TLD analysis
        analysis['suspicious_tld'] = analysis['tld'] in self.suspicious_tlds
        analysis['academic_domain'] = any(academic_tld in domain for academic_tld in self.academic_domains)
        
        # Check against legitimate publishers
        analysis['legitimate_publisher'] = any(legit_domain in domain for legit_domain in self.legitimate_publishers)
        
        # Typosquatting detection (basic)
        analysis['typosquatting_risk'] = self.check_typosquatting_risk(domain)
        
        # Set indicators and flags
        if analysis['legitimate_publisher']:
            analysis['legitimacy_indicators'].append('Known legitimate publisher')
        
        if analysis['academic_domain']:
            analysis['legitimacy_indicators'].append('Academic domain')
        
        if analysis['suspicious_tld']:
            analysis['warning_flags'].append('Suspicious TLD')
        
        if analysis['has_numbers']:
            analysis['warning_flags'].append('Contains numbers')
        
        if analysis['domain_length'] > 50:
            analysis['warning_flags'].append('Very long domain name')
        
        if analysis['typosquatting_risk']:
            analysis['warning_flags'].append('Possible typosquatting')
        
        return analysis
    
    def check_typosquatting_risk(self, domain: str) -> bool:
        """Check if domain might be typosquatting a legitimate publisher"""
        # Simple typosquatting detection
        for legit_domain in self.legitimate_publishers:
            if legit_domain in domain and domain != legit_domain:
                # Calculate similarity
                similarity = self.calculate_domain_similarity(domain, legit_domain)
                if similarity > 0.7:  # High similarity threshold
                    return True
        return False
    
    def calculate_domain_similarity(self, domain1: str, domain2: str) -> float:
        """Calculate similarity between two domains (simple Jaccard similarity)"""
        set1 = set(domain1.lower())
        set2 = set(domain2.lower())
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0
    
    def calculate_domain_risk_score(self, analysis: Dict) -> float:
        """Calculate overall domain risk score (0-100)"""
        risk_score = 0
        
        # Age-based scoring
        whois_info = analysis.get('whois_info', {})
        domain_age = whois_info.get('domain_age_days', 0)
        
        if domain_age is None or domain_age < 30:  # Very new domain
            risk_score += 30
        elif domain_age < 365:  # Less than 1 year
            risk_score += 15
        elif domain_age < 365 * 2:  # Less than 2 years
            risk_score += 5
        
        # TLD scoring
        if analysis.get('suspicious_tld', False):
            risk_score += 25
        
        # Academic domain bonus (negative risk)
        if analysis.get('academic_domain', False):
            risk_score -= 20
        
        # Legitimate publisher bonus (negative risk)
        if analysis.get('legitimate_publisher', False):
            risk_score -= 30
        
        # SSL scoring
        ssl_info = analysis.get('ssl_info', {})
        if not ssl_info.get('has_ssl', False):
            risk_score += 20
        elif ssl_info.get('self_signed', False):
            risk_score += 15
        
        # Privacy protection
        if whois_info.get('privacy_protected', False):
            risk_score += 10
        
        # Domain characteristics
        if analysis.get('has_numbers', False):
            risk_score += 5
        
        if analysis.get('has_hyphens', False):
            risk_score += 5
        
        if analysis.get('typosquatting_risk', False):
            risk_score += 25
        
        # DNS configuration
        dns_info = analysis.get('dns_info', {})
        if not dns_info.get('has_spf', False):
            risk_score += 5
        
        if dns_info.get('suspicious_mx', False):
            risk_score += 15
        
        # Registrar scoring
        if whois_info.get('suspicious_registrar', False):
            risk_score += 10
        
        # Ensure score is within bounds
        risk_score = max(0, min(risk_score, 100))
        
        return risk_score
    
    def get_domain_reputation(self, domain: str) -> Dict:
        """Get domain reputation from external sources (if available)"""
        reputation = {
            'safe_browsing': 'unknown',
            'virus_total': 'unknown',
            'reputation_score': 0
        }
        
        # Note: In a real implementation, you would integrate with:
        # - Google Safe Browsing API
        # - VirusTotal API
        # - Other reputation services
        
        # Placeholder for external API integrations
        try:
            # Google Safe Browsing (requires API key)
            # safe_browsing_result = self.check_safe_browsing(domain)
            # reputation['safe_browsing'] = safe_browsing_result
            
            # VirusTotal (requires API key)
            # virus_total_result = self.check_virus_total(domain)
            # reputation['virus_total'] = virus_total_result
            
            pass
            
        except Exception as e:
            reputation['error'] = str(e)
        
        return reputation

