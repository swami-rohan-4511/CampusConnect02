#!/usr/bin/env python3
"""
Campus Connect Health Monitoring Script
Comprehensive health checks for all services and performance monitoring
"""

import requests
import json
import time
import psutil
import sys
from datetime import datetime
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('health_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class HealthMonitor:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.services = {
            "api_gateway": f"{base_url}/health",
            "auth_service": f"{base_url}/auth/health",
            "meetups_service": f"{base_url}/meetups/health",
            "marketplace_service": f"{base_url}/marketplace/health",
            "stolen_found_service": f"{base_url}/stolen-found/health",
            "rooms_service": f"{base_url}/rooms/health",
            "rental_service": f"{base_url}/rental/health",
            "clubs_service": f"{base_url}/clubs/health",
            "jobs_service": f"{base_url}/jobs/health",
            "notes_service": f"{base_url}/notes/health",
            "food_service": f"{base_url}/food/health",
            "websocket_service": "http://localhost:8080/health"
        }

    def check_service_health(self, service_name: str, url: str) -> Dict[str, Any]:
        """Check health of a single service"""
        try:
            start_time = time.time()
            response = self.session.get(url, timeout=10)
            response_time = time.time() - start_time

            return {
                "service": service_name,
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time": round(response_time * 1000, 2),  # ms
                "status_code": response.status_code,
                "timestamp": datetime.utcnow().isoformat()
            }
        except requests.exceptions.RequestException as e:
            return {
                "service": service_name,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def check_all_services(self) -> Dict[str, Any]:
        """Check health of all services"""
        results = {}
        healthy_count = 0
        total_count = len(self.services)

        logger.info("Starting comprehensive health check...")

        for service_name, url in self.services.items():
            result = self.check_service_health(service_name, url)
            results[service_name] = result

            if result["status"] == "healthy":
                healthy_count += 1
                logger.info(f"✅ {service_name}: Healthy ({result.get('response_time', 'N/A')}ms)")
            else:
                logger.error(f"❌ {service_name}: Unhealthy - {result.get('error', 'Unknown error')}")

        # System metrics
        system_metrics = self.get_system_metrics()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "healthy" if healthy_count == total_count else "degraded",
            "healthy_services": healthy_count,
            "total_services": total_count,
            "services": results,
            "system_metrics": system_metrics
        }

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "memory_used_gb": round(psutil.virtual_memory().used / (1024**3), 2),
                "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "disk_usage_percent": psutil.disk_usage('/').percent,
                "network_connections": len(psutil.net_connections()),
            }
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {"error": str(e)}

    def check_database_connectivity(self) -> Dict[str, Any]:
        """Check database connectivity for all services"""
        db_checks = {}

        # This would require database credentials and connections
        # For now, return placeholder
        db_checks["auth_db"] = {"status": "unknown", "message": "Database check not implemented"}
        db_checks["meetups_db"] = {"status": "unknown", "message": "Database check not implemented"}
        # Add more database checks as needed

        return db_checks

    def check_external_services(self) -> Dict[str, Any]:
        """Check external service connectivity"""
        external_checks = {}

        # Redis check
        try:
            redis_response = self.session.get("http://localhost:6379/ping", timeout=5)
            external_checks["redis"] = {"status": "healthy", "response_time": "N/A"}
        except:
            external_checks["redis"] = {"status": "unhealthy", "error": "Connection failed"}

        # Add more external service checks (Cloudinary, Firebase, etc.)

        return external_checks

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive health report"""
        report = []
        report.append("=" * 60)
        report.append("CAMPUS CONNECT HEALTH REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {results['timestamp']}")
        report.append(f"Overall Status: {results['overall_status'].upper()}")
        report.append(f"Healthy Services: {results['healthy_services']}/{results['total_services']}")
        report.append("")

        # Service details
        report.append("SERVICE STATUS:")
        report.append("-" * 30)
        for service_name, service_data in results['services'].items():
            status_icon = "✅" if service_data['status'] == 'healthy' else "❌"
            response_time = service_data.get('response_time', 'N/A')
            report.append(f"{status_icon} {service_name}: {service_data['status']} ({response_time}ms)")

        report.append("")

        # System metrics
        if 'system_metrics' in results:
            report.append("SYSTEM METRICS:")
            report.append("-" * 30)
            metrics = results['system_metrics']
            report.append(f"CPU Usage: {metrics.get('cpu_percent', 'N/A')}%")
            report.append(f"Memory Usage: {metrics.get('memory_percent', 'N/A')}%")
            report.append(f"Memory Used: {metrics.get('memory_used_gb', 'N/A')} GB")
            report.append(f"Disk Usage: {metrics.get('disk_usage_percent', 'N/A')}%")

        report.append("=" * 60)

        return "\n".join(report)

    def monitor_continuous(self, interval: int = 60):
        """Continuous monitoring with specified interval"""
        logger.info(f"Starting continuous monitoring (interval: {interval}s)")

        try:
            while True:
                results = self.check_all_services()

                # Log summary
                status = results['overall_status']
                healthy = results['healthy_services']
                total = results['total_services']

                if status == 'healthy':
                    logger.info(f"✅ System healthy: {healthy}/{total} services operational")
                else:
                    logger.warning(f"⚠️  System degraded: {healthy}/{total} services operational")

                # Save detailed report
                report = self.generate_report(results)
                with open('health_report_latest.txt', 'w') as f:
                    f.write(report)

                time.sleep(interval)

        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Monitoring error: {e}")

def main():
    """Main function for command-line usage"""
    import argparse

    parser = argparse.ArgumentParser(description='Campus Connect Health Monitor')
    parser.add_argument('--url', default='http://localhost:8000', help='Base URL for services')
    parser.add_argument('--continuous', action='store_true', help='Run continuous monitoring')
    parser.add_argument('--interval', type=int, default=60, help='Monitoring interval in seconds')
    parser.add_argument('--report', action='store_true', help='Generate detailed report')

    args = parser.parse_args()

    monitor = HealthMonitor(args.url)

    if args.continuous:
        monitor.monitor_continuous(args.interval)
    elif args.report:
        results = monitor.check_all_services()
        report = monitor.generate_report(results)
        print(report)

        # Save to file
        with open('health_report.txt', 'w') as f:
            f.write(report)
        print("\nReport saved to health_report.txt")
    else:
        # Single check
        results = monitor.check_all_services()
        report = monitor.generate_report(results)
        print(report)

        # Exit with appropriate code
        if results['overall_status'] == 'healthy':
            sys.exit(0)
        else:
            sys.exit(1)

if __name__ == "__main__":
    main()