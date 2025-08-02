#!/usr/bin/env python3
"""
Database migration script for EduLearn platform
This script adds the new columns to existing tables
"""

import sys
import os
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.exc import OperationalError

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db

def add_moderation_columns():
    """Add moderation columns to existing tables"""
    print("Adding moderation columns to database tables...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Get the database engine
            engine = db.engine
            
            # Reflect the existing database tables
            metadata = MetaData()
            metadata.reflect(bind=engine)
            
            # Check if courses table exists
            if 'courses' in metadata.tables:
                courses_table = metadata.tables['courses']
                print("✓ Found courses table")
                
                # Check if columns already exist
                columns = [c.name for c in courses_table.c]
                
                # Add columns that don't exist
                columns_to_add = [
                    'is_approved', 'is_reported', 'is_removed', 'approved_by', 'approved_at',
                    'rejected_by', 'rejected_at', 'report_resolved_by', 'report_resolved_at',
                    'removed_by', 'removed_at', 'rejection_reason', 'report_resolution', 'removal_reason'
                ]
                
                # In a production environment, you would use Alembic for migrations
                # For this demo, we'll just note what needs to be done
                print("Note: In a production environment, you would run:")
                print("ALTER TABLE courses ADD COLUMN is_approved BOOLEAN DEFAULT 1;")
                print("ALTER TABLE courses ADD COLUMN is_reported BOOLEAN DEFAULT 0;")
                print("ALTER TABLE courses ADD COLUMN is_removed BOOLEAN DEFAULT 0;")
                # ... and so on for all columns
                
            else:
                print("Courses table not found")
                
            print("Migration check completed.")
            print("Note: This is a demonstration script. In a production environment, use proper migration tools like Alembic.")
            
        except Exception as e:
            print(f"Migration check failed: {e}")

def main():
    """Main function"""
    print("EduLearn Platform Database Migration Script")
    print("=" * 50)
    
    add_moderation_columns()

if __name__ == "__main__":
    main()
