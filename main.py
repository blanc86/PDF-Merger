#!/usr/bin/env python3
"""
PDF Merger Tool with Debugging
Merges multiple PDF files into a single PDF file
"""

import os
import sys
import time
import logging
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter

def setup_logging():
    """Set up logging configuration"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('pdf_merger_debug.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def check_system_requirements():
    """Check if system has required components"""
    logger = logging.getLogger(__name__)
    
    logger.info("Checking system requirements...")
    
    # Check Python version
    python_version = sys.version_info
    logger.debug(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check if PyPDF2 is importable
    try:
        import PyPDF2
        logger.debug(f"PyPDF2 version: {PyPDF2.__version__}")
    except ImportError as e:
        logger.error(f"PyPDF2 not installed: {e}")
        return False
    
    return True

def validate_directories(input_dir, output_dir):
    """Validate and create directories"""
    logger = logging.getLogger(__name__)
    
    logger.info("Validating directories...")
    logger.debug(f"Input directory path: {input_dir.absolute()}")
    logger.debug(f"Output directory path: {output_dir.absolute()}")
    
    # Create directories if they don't exist
    for directory in [input_dir, output_dir]:
        if not directory.exists():
            logger.info(f"Creating directory: {directory}")
            try:
                directory.mkdir(parents=True, exist_ok=True)
                logger.info(f"Directory created successfully: {directory}")
            except Exception as e:
                logger.error(f"Failed to create directory {directory}: {e}")
                return False
        else:
            logger.debug(f"Directory exists: {directory}")
    
    # Check permissions
    if not os.access(input_dir, os.R_OK):
        logger.error(f"No read permission for input directory: {input_dir}")
        return False
    
    if not os.access(output_dir, os.W_OK):
        logger.error(f"No write permission for output directory: {output_dir}")
        return False
    
    logger.info("Directory validation completed successfully")
    return True

def find_and_validate_pdf_files(input_dir):
    """Find and validate PDF files"""
    logger = logging.getLogger(__name__)
    
    logger.info("Searching for PDF files...")
    
    # Find all PDF files
    pdf_files = list(input_dir.glob("*.pdf"))
    logger.debug(f"Found {len(pdf_files)} PDF files")
    
    if not pdf_files:
        logger.warning("No PDF files found")
        all_files = list(input_dir.glob("*"))
        logger.debug(f"All files in directory: {[f.name for f in all_files]}")
        return []
    
    # Validate each file
    valid_files = []
    for pdf_file in pdf_files:
        logger.debug(f"Validating file: {pdf_file.name}")
        
        # Check if file is accessible
        if not pdf_file.exists():
            logger.warning(f"File doesn't exist: {pdf_file.name}")
            continue
            
        if not os.access(pdf_file, os.R_OK):
            logger.warning(f"No read permission for file: {pdf_file.name}")
            continue
            
        # Check file size
        file_size = pdf_file.stat().st_size
        logger.debug(f"File size: {file_size} bytes ({file_size / 1024:.2f} KB)")
        
        if file_size == 0:
            logger.warning(f"File is empty: {pdf_file.name}")
            continue
        
        # Try to open the PDF to check if it's valid
        try:
            reader = PdfReader(str(pdf_file))
            page_count = len(reader.pages)
            logger.debug(f"PDF pages: {page_count}")
            
            if page_count == 0:
                logger.warning(f"PDF has no pages: {pdf_file.name}")
                continue
                
            valid_files.append(pdf_file)
            logger.debug(f"File validated: {pdf_file.name}")
            
        except Exception as e:
            logger.warning(f"Invalid PDF file: {pdf_file.name} - {str(e)}")
            continue
    
    logger.info(f"Validation complete: {len(valid_files)} valid files out of {len(pdf_files)} found")
    return valid_files

def sort_files_by_preference(pdf_files):
    """Sort PDF files by name (alphabetically)"""
    logger = logging.getLogger(__name__)
    
    logger.info("Sorting PDF files alphabetically...")
    sorted_files = sorted(pdf_files, key=lambda x: x.name.lower())
    
    logger.info("File order for merging:")
    for i, pdf_file in enumerate(sorted_files, 1):
        logger.info(f"  {i}. {pdf_file.name}")
    
    return sorted_files

def merge_pdf_files(pdf_files, output_file):
    """Merge multiple PDF files into one"""
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting PDF merge process...")
    logger.info(f"Output file: {output_file.name}")
    
    start_time = time.time()
    writer = PdfWriter()
    
    total_pages = 0
    file_info = []
    
    try:
        for i, pdf_file in enumerate(pdf_files, 1):
            logger.info(f"[{i}/{len(pdf_files)}] Processing: {pdf_file.name}")
            
            try:
                reader = PdfReader(str(pdf_file))
                page_count = len(reader.pages)
                
                logger.debug(f"Adding {page_count} pages from {pdf_file.name}")
                
                # Add all pages from this PDF
                for page_num in range(page_count):
                    page = reader.pages[page_num]
                    writer.add_page(page)
                
                total_pages += page_count
                file_info.append({
                    'filename': pdf_file.name,
                    'pages': page_count,
                    'file_size': pdf_file.stat().st_size
                })
                
                logger.info(f"✓ Added {page_count} pages from {pdf_file.name}")
                
            except Exception as e:
                logger.error(f"✗ Failed to process {pdf_file.name}: {str(e)}")
                continue
        
        # Write the merged PDF
        logger.info(f"Writing merged PDF with {total_pages} total pages...")
        
        with open(output_file, 'wb') as output_stream:
            writer.write(output_stream)
        
        end_time = time.time()
        merge_time = round(end_time - start_time, 2)
        
        # Verify output file
        if output_file.exists():
            output_size = output_file.stat().st_size
            logger.info(f"✓ Merge completed successfully!")
            logger.info(f"✓ Output file: {output_file.name}")
            logger.info(f"✓ Total pages: {total_pages}")
            logger.info(f"✓ Output size: {output_size} bytes ({output_size / 1024:.2f} KB)")
            logger.info(f"✓ Merge time: {merge_time} seconds")
            
            return {
                'success': True,
                'output_file': output_file.name,
                'total_pages': total_pages,
                'total_files': len(pdf_files),
                'output_size': output_size,
                'merge_time': merge_time,
                'file_info': file_info
            }
        else:
            logger.error("Merge appeared to succeed but output file not found")
            return {
                'success': False,
                'error': 'Output file not created'
            }
            
    except Exception as e:
        end_time = time.time()
        merge_time = round(end_time - start_time, 2)
        
        logger.error(f"✗ Merge failed: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        
        return {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }

def get_output_filename(input_dir):
    """Generate output filename based on input directory or user preference"""
    logger = logging.getLogger(__name__)
    
    # Default filename with timestamp
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    default_name = f"merged_pdf_{timestamp}.pdf"
    
    logger.info(f"Default output filename: {default_name}")
    
    # You can add user input here if desired
    # user_input = input(f"Enter output filename (or press Enter for default '{default_name}'): ").strip()
    # if user_input:
    #     if not user_input.endswith('.pdf'):
    #         user_input += '.pdf'
    #     return user_input
    
    return default_name

def merge_pdfs():
    """Main function to merge PDF files"""
    logger = setup_logging()
    
    logger.info("=" * 60)
    logger.info("PDF Merger Tool Started")
    logger.info("=" * 60)
    
    # Check system requirements
    if not check_system_requirements():
        logger.error("System requirements not met. Exiting.")
        return
    
    # Define directories
    input_dir = Path("input")
    output_dir = Path("output")
    
    # Validate directories
    if not validate_directories(input_dir, output_dir):
        logger.error("Directory validation failed. Exiting.")
        return
    
    # Find and validate PDF files
    pdf_files = find_and_validate_pdf_files(input_dir)
    
    if not pdf_files:
        logger.error("No valid PDF files found in the input directory!")
        logger.info(f"Please place your PDF files in: {input_dir.absolute()}")
        return
    
    if len(pdf_files) < 2:
        logger.warning("Only one PDF file found. At least 2 files are needed for merging.")
        logger.info("If you want to copy the single file, it will be copied to output directory.")
        
        # Copy single file to output
        single_file = pdf_files[0]
        output_file = output_dir / single_file.name
        
        try:
            import shutil
            shutil.copy2(single_file, output_file)
            logger.info(f"✓ Single file copied: {output_file.name}")
        except Exception as e:
            logger.error(f"✗ Failed to copy file: {str(e)}")
        
        return
    
    # Sort files
    sorted_files = sort_files_by_preference(pdf_files)
    
    # Generate output filename
    output_filename = get_output_filename(input_dir)
    output_file = output_dir / output_filename
    
    # Merge PDF files
    result = merge_pdf_files(sorted_files, output_file)
    
    # Print summary
    print_merge_summary(result, logger)

def print_merge_summary(result, logger):
    """Print detailed merge summary"""
    logger.info("-" * 60)
    logger.info("MERGE SUMMARY")
    logger.info("-" * 60)
    
    if result['success']:
        logger.info(f"✓ Merge Status: SUCCESS")
        logger.info(f"✓ Output File: {result['output_file']}")
        logger.info(f"✓ Total Files Merged: {result['total_files']}")
        logger.info(f"✓ Total Pages: {result['total_pages']}")
        logger.info(f"✓ Output Size: {result['output_size'] / 1024:.2f} KB")
        logger.info(f"✓ Merge Time: {result['merge_time']} seconds")
        
        logger.info("\nFile Details:")
        for info in result['file_info']:
            logger.info(f"  • {info['filename']}: {info['pages']} pages ({info['file_size'] / 1024:.2f} KB)")
    else:
        logger.error(f"✗ Merge Status: FAILED")
        logger.error(f"✗ Error: {result['error']}")
    
    logger.info("=" * 60)
    logger.info("Debug log saved to: pdf_merger_debug.log")
    logger.info("=" * 60)

if __name__ == "__main__":
    try:
        merge_pdfs()
    except KeyboardInterrupt:
        print("\nMerge cancelled by user.")
        logging.info("Merge cancelled by user")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        logging.error(f"Unexpected error: {str(e)}", exc_info=True)
