#!/usr/bin/env python3
"""Price the AWS plan from the live AWS Price List API (on-demand, Linux, shared tenancy).

    python3 scripts/aws-cost-estimate.py --region us-east-1 [--app r6i.xlarge --gpu g6.xlarge --db db.t4g.small]
"""
from __future__ import annotations

import argparse
import json
import subprocess

LOCATION = {"us-east-1": "US East (N. Virginia)", "us-east-2": "US East (Ohio)", "us-west-2": "US West (Oregon)",
            "eu-west-1": "EU (Ireland)", "eu-central-1": "EU (Frankfurt)", "ap-southeast-1": "Asia Pacific (Singapore)"}


def price(service: str, filters: dict[str, str]) -> float:
    args = ["aws", "pricing", "get-products", "--region", "us-east-1", "--service-code", service, "--max-items", "20", "--output", "json", "--filters"]
    args += [f"Type=TERM_MATCH,Field={k},Value={v}" for k, v in filters.items()]
    data = json.loads(subprocess.run(args, capture_output=True, text=True, check=True).stdout)
    for raw in data.get("PriceList", []):
        item = json.loads(raw)
        for term in item.get("terms", {}).get("OnDemand", {}).values():
            for dim in term["priceDimensions"].values():
                usd = float(dim["pricePerUnit"].get("USD", 0))
                if usd > 0:
                    return usd
    raise RuntimeError(f"no price for {service} {filters}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--region", default="us-east-1")
    p.add_argument("--app", default="r6i.xlarge")
    p.add_argument("--gpu", default="g6.xlarge", help="GPU instance type, or none for the CPU-only variant")
    p.add_argument("--db", default="db.t4g.small")
    p.add_argument("--app-disk", type=int, default=80)
    p.add_argument("--gpu-disk", type=int, default=120)
    p.add_argument("--db-disk", type=int, default=20)
    a = p.parse_args()
    loc = LOCATION[a.region]
    ec2 = {"location": loc, "operatingSystem": "Linux", "tenancy": "Shared", "preInstalledSw": "NA", "capacitystatus": "Used"}
    app = price("AmazonEC2", {**ec2, "instanceType": a.app})
    no_gpu = a.gpu.lower() in ("", "none")
    gpu = 0.0 if no_gpu else price("AmazonEC2", {**ec2, "instanceType": a.gpu})
    ips = 1 if no_gpu else 2  # public IPv4 addresses: app EIP (+ GPU VM)
    if no_gpu:
        a.gpu_disk = 0
    db = price("AmazonRDS", {"location": loc, "instanceType": a.db, "databaseEngine": "PostgreSQL", "deploymentOption": "Single-AZ"})
    gp3 = price("AmazonEC2", {"location": loc, "volumeApiName": "gp3", "productFamily": "Storage"})
    rds_gp3 = price("AmazonRDS", {"location": loc, "volumeType": "General Purpose-GP3", "deploymentOption": "Single-AZ", "databaseEngine": "PostgreSQL"})
    ipv4 = 0.005  # USD per public IPv4 address-hour (AWS VPC pricing, Feb 2024)
    secrets = 0.40  # per secret-month
    hourly_compute = app + gpu + db + ips * ipv4
    monthly_storage = gp3 * (a.app_disk + a.gpu_disk) + rds_gp3 * a.db_disk
    rows = {
        "app_vm_per_hour": app, "gpu_vm_per_hour": gpu, "rds_per_hour": db, "public_ipv4_per_hour": ips * ipv4,
        "ebs_gp3_per_gb_month": gp3, "rds_gp3_per_gb_month": rds_gp3,
    }
    est = {
        "running_per_hour": round(hourly_compute, 4),
        "storage_per_month": round(monthly_storage + secrets, 2),
        "8h_demo_day": round(8 * hourly_compute + (monthly_storage + secrets) / 30, 2),
        "24h_day": round(24 * hourly_compute + (monthly_storage + secrets) / 30, 2),
        "workshop_176h_month": round(176 * hourly_compute + monthly_storage + secrets, 2),
        "always_on_730h_month": round(730 * hourly_compute + monthly_storage + secrets, 2),
        "stopped_vms_per_month": round(db * 730 + ips * ipv4 * 730 + monthly_storage + secrets, 2),
    }
    print(json.dumps({"region": a.region, "unit_prices_usd": rows, "estimates_usd": est,
                      "excluded": "data transfer out, CloudWatch beyond free tier, ECR storage (~$0.10/GB-month), S3 (cents), taxes"}, indent=1))


if __name__ == "__main__":
    main()
