#!/usr/bin/env python3
"""
Admin User Creation Script for Sales Engagement Platform

This script creates an admin user directly in the database.
Run this script to create the initial admin user for your platform.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.user import User, UserRole
from app.models.company import Company
from app.core.security import get_password_hash


async def create_admin_user():
    """Create an admin user in the database"""
    
    # Database connection
    engine = create_async_engine(settings.effective_database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # Admin user details
            admin_email = "admin@salesengagement.com"
            admin_password = "Admin123!@#"  # Change this!
            company_name = "Sales Engagement Platform"
            
            print(f"Creating admin user: {admin_email}")
            
            # Check if admin already exists
            existing_user = await session.execute(
                select(User).where(User.email == admin_email)
            )
            if existing_user.scalar_one_or_none():
                print(f"❌ Admin user {admin_email} already exists!")
                return
            
            # Create company first
            company = Company(
                name=company_name,
                domain="salesengagement.com",
                is_active=True
            )
            session.add(company)
            await session.flush()  # Get company ID
            
            # Create admin user
            admin_user = User(
                email=admin_email,
                hashed_password=get_password_hash(admin_password),
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True,
                tenant_id=company.id,
                company_id=company.id
            )
            
            session.add(admin_user)
            await session.commit()
            
            print("✅ Admin user created successfully!")
            print(f"📧 Email: {admin_email}")
            print(f"🔑 Password: {admin_password}")
            print(f"🏢 Company: {company_name}")
            print(f"👑 Role: {admin_user.role.value}")
            print("\n⚠️  IMPORTANT: Change the password after first login!")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error creating admin user: {e}")
            raise
        finally:
            await engine.dispose()


async def promote_user_to_admin(email: str):
    """Promote an existing user to admin role"""
    
    engine = create_async_engine(settings.effective_database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            from sqlalchemy import select
            
            # Find user
            result = await session.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                print(f"❌ User {email} not found!")
                return
            
            # Promote to admin
            user.role = UserRole.ADMIN
            user.is_active = True
            user.is_verified = True
            
            await session.commit()
            
            print(f"✅ User {email} promoted to admin!")
            print(f"👑 New role: {user.role.value}")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error promoting user: {e}")
            raise
        finally:
            await engine.dispose()


async def list_users():
    """List all users in the system"""
    
    engine = create_async_engine(settings.effective_database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            from sqlalchemy import select
            
            result = await session.execute(
                select(User).order_by(User.created_at.desc())
            )
            users = result.scalars().all()
            
            if not users:
                print("No users found in the system.")
                return
            
            print(f"\n📋 Found {len(users)} users:")
            print("-" * 80)
            for user in users:
                status = "✅ Active" if user.is_active else "❌ Inactive"
                verified = "✅ Verified" if user.is_verified else "❌ Unverified"
                print(f"📧 {user.email:<30} 👑 {user.role.value:<10} {status} {verified}")
            
        except Exception as e:
            print(f"❌ Error listing users: {e}")
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Admin User Management")
    parser.add_argument("action", choices=["create", "promote", "list"], 
                       help="Action to perform")
    parser.add_argument("--email", help="Email address for promote action")
    
    args = parser.parse_args()
    
    if args.action == "create":
        asyncio.run(create_admin_user())
    elif args.action == "promote":
        if not args.email:
            print("❌ Email required for promote action. Use --email user@example.com")
            sys.exit(1)
        asyncio.run(promote_user_to_admin(args.email))
    elif args.action == "list":
        asyncio.run(list_users())