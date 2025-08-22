import os
import uuid
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, redirect, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.config import Config
from werkzeug.utils import secure_filename
from app.models.user import User, db
from app.models.evaluation import Evaluation, EvaluationStatus
from app.services.local_storage_service import LocalStorageService
from app.services.excel_parser import ExcelParser
from app.services.pdf_parser import PDFParser
from app.services.docx_parser import DOCXParser
from app.services.gpt_evaluator import GPTEvaluator
from app.services.pdf_generator import PDFGenerator
from app.services.email_service import EmailService
from app.services.template_evaluator import TemplateEvaluator

logger = logging.getLogger(__name__)

# Create the upload blueprint
upload_bp = Blueprint('upload', __name__)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@upload_bp.route('/evaluate', methods=['POST'])
@jwt_required()
def evaluate_document():
    """
    Main evaluation endpoint for document upload and evaluation with multiple methods
    """
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if file was selected
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only .pdf and .docx files are allowed'}), 400
        
        # Get evaluation methods and templates from form data
        evaluation_methods = request.form.getlist('evaluation_methods') or ['basic']
        selected_templates = request.form.getlist('selected_templates') or []
        
        # Ensure basic is always included if no methods specified
        if not evaluation_methods:
            evaluation_methods = ['basic']
        
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
        
        # Save file temporarily first
        upload_folder = Config.UPLOAD_FOLDER
        os.makedirs(upload_folder, exist_ok=True)
        temp_file_path = os.path.join(upload_folder, unique_filename)
        
        try:
            file.save(temp_file_path)
            logger.info(f"File saved temporarily: {temp_file_path}")
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            return jsonify({'error': 'Failed to save uploaded file'}), 500
        
        # Upload file to local storage using LocalStorageService
        storage_service = LocalStorageService()
        original_file_key = f"original_files/{unique_filename}"
        
        try:
            storage_service.upload_file(temp_file_path, original_file_key)
            logger.info(f"Original file uploaded to local storage: {original_file_key}")
        except Exception as e:
            logger.error(f"Failed to upload original file to local storage: {e}")
            # Continue with temporary file if local storage upload fails
        
        # Create evaluation record
        evaluation = Evaluation(
            user_id=current_user_id,
            original_filename=original_filename,
            original_file_s3_key=original_file_key,
            status=EvaluationStatus.PROCESSING,
            file_size=os.path.getsize(temp_file_path),
            expires_at=datetime.utcnow() + timedelta(hours=Config.REPORT_EXPIRY_HOURS),
            evaluation_methods=evaluation_methods,
            selected_templates=selected_templates
        )
        
        db.session.add(evaluation)
        db.session.commit()
        
        logger.info(f"Starting evaluation for user {current_user_id}, evaluation ID: {evaluation.id}")
        logger.info(f"Evaluation methods: {evaluation_methods}, Templates: {selected_templates}")
        
        db.session.add(evaluation)
        db.session.commit()
        
        try:
            # Extract text content based on file type
            text_content = ""
            
            if file_extension == 'pdf':
                pdf_parser = PDFParser()
                parse_result = pdf_parser.parse_pdf_file(temp_file_path)
                text_content = parse_result['text_content']
            elif file_extension == 'docx':
                docx_parser = DOCXParser()
                parse_result = docx_parser.parse_docx_file(temp_file_path)
                text_content = parse_result['text_content']
            
            # Check if we got any text content
            if not text_content or len(text_content.strip()) < 50:
                evaluation.status = EvaluationStatus.FAILED
                evaluation.error_message = 'Unable to extract text from document. Please ensure the document contains readable text.'
                db.session.commit()
                return jsonify({
                    'error': 'Unable to extract text from document. Please ensure the document contains readable text.'
                }), 400
            
            evaluation.text_length = len(text_content)
            
            # Perform evaluation based on selected methods
            evaluation_results = perform_multi_method_evaluation(
                text_content, 
                evaluation_methods, 
                selected_templates, 
                current_user_id
            )
            
            if not evaluation_results or 'categories' not in evaluation_results:
                raise Exception("Invalid evaluation results received")
        except Exception as eval_error:
            logger.error(f"Evaluation failed: {eval_error}")
            evaluation.status = EvaluationStatus.FAILED
            evaluation.error_message = f'Evaluation failed: {str(eval_error)}'
            db.session.commit()
            return jsonify({
                'error': f'Evaluation failed: {str(eval_error)}'
            }), 500
        
        # Update evaluation with results
        evaluation.evaluation_results = evaluation_results
        evaluation.evaluated_at = datetime.utcnow()
        
        # Extract individual scores
        categories = evaluation_results.get('categories', {})
        evaluation.line_editing_score = categories.get('line-editing', {}).get('score')
        evaluation.plot_score = categories.get('plot', {}).get('score')
        evaluation.character_score = categories.get('character', {}).get('score')
        evaluation.flow_score = categories.get('flow', {}).get('score')
        evaluation.worldbuilding_score = categories.get('worldbuilding', {}).get('score')
        evaluation.readiness_score = categories.get('readiness', {}).get('score')
        
        # Calculate overall score
        evaluation.calculate_overall_score()
        
        # Generate PDF report
        pdf_generator = PDFGenerator()
        report_filename = f"evaluation_report_{evaluation.id}_{uuid.uuid4().hex}.pdf"
        report_path = os.path.join(upload_folder, report_filename)
        
        metadata = {
            'original_filename': original_filename,
            'file_type': file_extension,
            'evaluation_date': datetime.now().isoformat(),
            'evaluation_id': evaluation.id
        }
        
        pdf_generator.generate_evaluation_report(evaluation_results, metadata, report_path)
        
        # Upload report to local storage
        download_url = None
        storage_service = LocalStorageService()
        try:
            file_key = f"reports/{report_filename}"
            storage_service.upload_file(report_path, file_key)
            download_url = storage_service.generate_download_url(file_key, expiration_hours=1)  # 1 hour
            evaluation.report_file_s3_key = file_key
            evaluation.download_url = download_url
            logger.info("Report uploaded to local storage successfully")
        except Exception as e:
            logger.error(f"Failed to upload report to local storage: {e}")
            # Fall back to direct file path
            evaluation.report_file_s3_key = f"reports/{report_filename}"
            evaluation.download_url = f"/api/upload/public/download-file/reports/{report_filename}"
        
        # Mark evaluation as completed
        evaluation.status = EvaluationStatus.COMPLETED
        db.session.commit()
        
        # Clean up temporary files
        try:
            os.remove(temp_file_path)
            if os.path.exists(report_path):
                os.remove(report_path)
        except Exception as e:
            logger.warning(f"Failed to clean up temporary files: {e}")
        
        # Return success response
        return jsonify({
            'success': True,
            'evaluation_id': evaluation.id,
            'message': 'Document evaluation completed successfully',
            'download_url': download_url,
            'results': evaluation_results
        }), 200
        
    except Exception as e:
        logger.error(f"Error during evaluation: {e}")
        evaluation.status = EvaluationStatus.FAILED
        evaluation.error_message = str(e)
        db.session.commit()
        
        # Clean up temporary file
        try:
            os.remove(temp_file_path)
        except:
            pass
        
        return jsonify({
            'error': 'Evaluation failed',
            'message': str(e)
        }), 500
            
    except Exception as e:
        logger.error(f"Unexpected error in evaluate_document: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@upload_bp.route('/evaluation/<int:evaluation_id>', methods=['GET'])
@jwt_required()
def get_evaluation(evaluation_id):
    """Get evaluation results by ID"""
    try:
        current_user_id = get_jwt_identity()
        
        evaluation = Evaluation.query.filter_by(
            id=evaluation_id, 
            user_id=current_user_id
        ).first()
        
        if not evaluation:
            return jsonify({'error': 'Evaluation not found'}), 404
        
        return jsonify({
            'evaluation': evaluation.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting evaluation: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@upload_bp.route('/evaluation/<int:evaluation_id>/download', methods=['GET'])
@jwt_required()
def download_evaluation(evaluation_id):
    """Download evaluation report with fresh AWS4 signature"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get evaluation
        evaluation = Evaluation.query.filter_by(
            id=evaluation_id,
            user_id=current_user_id
        ).first()
        
        if not evaluation:
            return jsonify({'error': 'Evaluation not found'}), 404
        
        if evaluation.status != EvaluationStatus.COMPLETED:
            return jsonify({'error': 'Evaluation not completed'}), 400
        
        # Generate fresh download URL
        storage_service = LocalStorageService()
        if evaluation.report_file_s3_key:
            # Use local file URL
            download_url = f"/api/upload/public/download-file/{evaluation.report_file_s3_key}"
            
            # Update the evaluation with the new URL
            evaluation.download_url = download_url
            db.session.commit()
            
            return jsonify({
                'download_url': download_url,
                'expires_in': '1 hour'
            }), 200
        else:
            return jsonify({'error': 'No report file available'}), 404
            
    except Exception as e:
        logger.error(f"Error downloading evaluation: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@upload_bp.route('/public/download/<path:file_key>', methods=['GET'])
def public_download(file_key):
    """Public download endpoint that doesn't require authentication"""
    try:
        # Validate file key format (should be like 'reports/filename.pdf')
        if not file_key or '..' in file_key or not file_key.startswith('reports/'):
            return jsonify({'error': 'Invalid file key'}), 400
        
        # Generate local file URL
        storage_service = LocalStorageService()
        download_url = storage_service.regenerate_download_url(file_key, expiration_hours=1)
        
        # Return the local file URL
        return jsonify({
            'download_url': download_url,
            'expires_in': '1 hour'
        }), 200
        
    except Exception as e:
        logger.error(f"Error in public download: {e}")
        return jsonify({'error': 'File not found or download failed'}), 404

@upload_bp.route('/public/download-file/<path:file_key>', methods=['GET'])
def public_download_file(file_key):
    """Public direct file download endpoint for local files when S3 is not available"""
    try:
        # Validate file key format (should be like 'reports/filename.pdf')
        if not file_key or '..' in file_key or not file_key.startswith('reports/'):
            return jsonify({'error': 'Invalid file key'}), 400
        
        # Extract filename from the key
        filename = file_key.split('/')[-1]
        local_file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
        
        # Check if file exists locally
        if not os.path.exists(local_file_path):
            logger.error(f"Local file not found: {local_file_path}")
            return jsonify({'error': 'File not found'}), 404
        
        # Read file content
        with open(local_file_path, 'rb') as f:
            file_content = f.read()
        
        # Check if content looks like a PDF
        if len(file_content) > 4 and file_content[:4] == b'%PDF':
            logger.info(f"Serving local PDF file: {filename}, size: {len(file_content)} bytes")
        else:
            logger.warning(f"Local file does not appear to be valid PDF: {filename}")
        
        # Create Flask response with file content
        flask_response = Response(
            file_content,
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Length': str(len(file_content)),
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        )
        
        return flask_response
        
    except Exception as e:
        logger.error(f"Error in public download file: {e}")
        return jsonify({'error': 'File not found or download failed'}), 404

@upload_bp.route('/public/redirect/<path:file_key>', methods=['GET'])
def public_redirect_download(file_key):
    """Public redirect endpoint that directly redirects to S3 URL"""
    try:
        # Validate file key format (should be like 'reports/filename.pdf')
        if not file_key or '..' in file_key or not file_key.startswith('reports/'):
            return jsonify({'error': 'Invalid file key'}), 400
        
        # Generate download URL for local storage
        storage_service = LocalStorageService()
        download_url = storage_service.regenerate_download_url(file_key, expiration_hours=1)
        
        # Redirect directly to the download URL
        return redirect(download_url, code=302)
        
    except Exception as e:
        logger.error(f"Error in public redirect download: {e}")
        return jsonify({'error': 'File not found or download failed'}), 404

@upload_bp.route('/public/test', methods=['GET'])
def public_test():
    """Test endpoint to verify public access works"""
    return jsonify({
        'message': 'Public endpoint is working',
        'timestamp': datetime.now().isoformat()
    }), 200

@upload_bp.route('/public/evaluation/<int:evaluation_id>/download', methods=['GET'])
def public_evaluation_download(evaluation_id):
    """Public download endpoint for evaluation reports - no authentication required"""
    try:
        # Get evaluation by ID (no user restriction)
        evaluation = Evaluation.query.filter_by(id=evaluation_id).first()
        
        if not evaluation:
            return jsonify({'error': 'Evaluation not found'}), 404
        
        if evaluation.status != EvaluationStatus.COMPLETED:
            return jsonify({'error': 'Evaluation not completed'}), 400
        
        if not evaluation.report_file_s3_key:
            return jsonify({'error': 'No report file available'}), 404
        
        # Generate fresh download URL for local storage
        storage_service = LocalStorageService()
        download_url = storage_service.regenerate_download_url(evaluation.report_file_s3_key, expiration_hours=24)
        
        # Update the evaluation with the new URL
        evaluation.download_url = download_url
        db.session.commit()
        
        # Return the download URL
        return jsonify({
            'download_url': download_url,
            'expires_in': '24 hours',
            'filename': evaluation.original_filename,
            'evaluation_id': evaluation.id
        }), 200
            
    except Exception as e:
        logger.error(f"Error in public evaluation download: {e}")
        return jsonify({'error': 'Download failed'}), 500

@upload_bp.route('/public/evaluation/<int:evaluation_id>/download-file', methods=['GET'])
def public_evaluation_download_file(evaluation_id):
    """Public direct file download endpoint - serves file content directly"""
    try:
        # Get evaluation by ID (no user restriction)
        evaluation = Evaluation.query.filter_by(id=evaluation_id).first()
        
        if not evaluation:
            return jsonify({'error': 'Evaluation not found'}), 404
        
        if evaluation.status != EvaluationStatus.COMPLETED:
            return jsonify({'error': 'Evaluation not completed'}), 400
        
        if not evaluation.report_file_s3_key:
            return jsonify({'error': 'No report file available'}), 404
        
        # Get the file from local storage
        storage_service = LocalStorageService()
        file_content = None
        source = 'local'
        
        try:
            # Get file content from local storage
            file_content = storage_service.get_file_content(evaluation.report_file_s3_key)
            logger.info(f"Downloading PDF from local storage: {evaluation.report_file_s3_key}, size: {len(file_content)} bytes")
        except Exception as local_error:
            logger.error(f"Local file download error: {local_error}")
            # Try fallback to direct file path
            filename = evaluation.report_file_s3_key.split('/')[-1]
            local_file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
            
            if os.path.exists(local_file_path):
                try:
                    with open(local_file_path, 'rb') as f:
                        file_content = f.read()
                    logger.info(f"Downloading PDF from fallback local path: {local_file_path}, size: {len(file_content)} bytes")
                except Exception as fallback_error:
                    logger.error(f"Fallback local file download error: {fallback_error}")
        
        # If we have file content, serve it
        if file_content:
            # Check if content looks like a PDF (should start with %PDF)
            if len(file_content) > 4 and file_content[:4] == b'%PDF':
                logger.info(f"File content appears to be valid PDF (source: {source})")
            else:
                logger.warning(f"File content does not appear to be valid PDF (source: {source})")
            
            # Create Flask response with file content
            flask_response = Response(
                file_content,
                mimetype='application/pdf',
                headers={
                    'Content-Disposition': f'attachment; filename="evaluation_{evaluation_id}.pdf"',
                    'Content-Length': str(len(file_content)),
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET',
                    'Access-Control-Allow-Headers': 'Content-Type'
                }
            )
            
            return flask_response
        
        # If no file content found, return error
        return jsonify({'error': 'File not found locally or in S3'}), 404
            
    except Exception as e:
        logger.error(f"Error in public evaluation download file: {e}")
        return jsonify({'error': 'Download failed'}), 500

@upload_bp.route('/public/evaluation/<int:evaluation_id>/redirect', methods=['GET'])
def public_evaluation_redirect(evaluation_id):
    """Public redirect endpoint for evaluation reports - direct download"""
    try:
        # Get evaluation by ID (no user restriction)
        evaluation = Evaluation.query.filter_by(id=evaluation_id).first()
        
        if not evaluation:
            return jsonify({'error': 'Evaluation not found'}), 404
        
        if evaluation.status != EvaluationStatus.COMPLETED:
            return jsonify({'error': 'Evaluation not completed'}), 400
        
        if not evaluation.report_file_s3_key:
            return jsonify({'error': 'No report file available'}), 404
        
        # Generate fresh download URL for local storage
        storage_service = LocalStorageService()
        download_url = storage_service.regenerate_download_url(evaluation.report_file_s3_key, expiration_hours=24)
        
        # Update the evaluation with the new URL
        evaluation.download_url = download_url
        db.session.commit()
        
        # Create response with proper headers for file download
        response = redirect(download_url, code=302)
        response.headers['Content-Disposition'] = f'attachment; filename="evaluation_{evaluation_id}.pdf"'
        response.headers['Content-Type'] = 'application/pdf'
        
        return response
            
    except Exception as e:
        logger.error(f"Error in public evaluation redirect: {e}")
        return jsonify({'error': 'Download failed'}), 500

@upload_bp.route('/public/evaluations', methods=['GET'])
def public_evaluations_list():
    """Public endpoint to list all completed evaluations"""
    try:
        # Get all completed evaluations (no user restriction)
        evaluations = Evaluation.query.filter_by(status=EvaluationStatus.COMPLETED).all()
        
        evaluations_list = []
        for evaluation in evaluations:
            evaluations_list.append({
                'id': evaluation.id,
                'filename': evaluation.original_filename,
                'created_at': evaluation.created_at.isoformat(),
                'overall_score': evaluation.overall_score,
                'download_url': f"/api/upload/public/evaluation/{evaluation.id}/redirect"
            })
        
        return jsonify({
            'evaluations': evaluations_list,
            'count': len(evaluations_list)
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing public evaluations: {e}")
        return jsonify({'error': 'Failed to list evaluations'}), 500

@upload_bp.route('/test-local-storage', methods=['GET'])
def test_local_storage():
    """Test endpoint to verify local storage functionality"""
    try:
        storage_service = LocalStorageService()
        
        # Generate a test URL
        test_url = storage_service.regenerate_download_url('test-file.pdf', expiration_hours=1)
        
        return jsonify({
            'message': 'Local storage test completed',
            'test_url': test_url,
            'base_path': storage_service.base_path,
            'storage_type': 'local'
        }), 200
        
    except Exception as e:
        return jsonify({
            'message': 'Local storage test failed',
            'error': str(e),
            'storage_type': 'local'
        }), 500

@upload_bp.route('/public/evaluation/<int:evaluation_id>/test-pdf', methods=['GET'])
def test_pdf_content(evaluation_id):
    """Test endpoint to check PDF content and metadata"""
    try:
        # Get evaluation by ID (no user restriction)
        evaluation = Evaluation.query.filter_by(id=evaluation_id).first()
        
        if not evaluation:
            return jsonify({'error': 'Evaluation not found'}), 404
        
        if evaluation.status != EvaluationStatus.COMPLETED:
            return jsonify({'error': 'Evaluation not completed'}), 400
        
        if not evaluation.report_file_s3_key:
            return jsonify({'error': 'No report file available'}), 404
        
        # Get the file from local storage
        storage_service = LocalStorageService()
        
        try:
            # Get file content from local storage
            file_content = storage_service.get_file_content(evaluation.report_file_s3_key)
            
            # Check if content looks like a PDF
            is_pdf = len(file_content) > 4 and file_content[:4] == b'%PDF'
            first_bytes = file_content[:20].hex() if len(file_content) >= 20 else file_content.hex()
            
            return jsonify({
                'success': True,
                'file_info': {
                    'file_key': evaluation.report_file_s3_key,
                    'file_size_bytes': len(file_content),
                    'is_pdf': is_pdf,
                    'first_20_bytes_hex': first_bytes,
                    'first_20_bytes_ascii': file_content[:20].decode('ascii', errors='ignore'),
                    'storage_type': 'local'
                }
            }), 200
            
        except Exception as local_error:
            logger.error(f"Local storage test error: {local_error}")
            return jsonify({
                'success': False,
                'error': f'Local storage access failed: {str(local_error)}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in PDF test: {e}")
        return jsonify({'error': 'Test failed'}), 500

@upload_bp.route('/clear-old-download-urls', methods=['POST'])
@jwt_required()
def clear_old_download_urls():
    """Clear old download URLs to force fresh AWS4 signature generation"""
    try:
        current_user_id = get_jwt_identity()
        
        # Clear download URLs for all user's evaluations
        evaluations = Evaluation.query.filter_by(user_id=current_user_id).all()
        
        for evaluation in evaluations:
            evaluation.download_url = None
        
        db.session.commit()
        
        logger.info(f"Cleared old download URLs for user {current_user_id}")
        
        return jsonify({
            'message': 'Old download URLs cleared successfully',
            'count': len(evaluations)
        }), 200
        
    except Exception as e:
        logger.error(f"Error clearing download URLs: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to clear download URLs'}), 500

@upload_bp.route('/evaluation/<int:evaluation_id>/direct-download', methods=['GET'])
@jwt_required()
def direct_download_evaluation(evaluation_id):
    """Direct download evaluation report - always generates fresh AWS4 signature"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get evaluation
        evaluation = Evaluation.query.filter_by(
            id=evaluation_id,
            user_id=current_user_id
        ).first()
        
        if not evaluation:
            return jsonify({'error': 'Evaluation not found'}), 404
        
        if evaluation.status != EvaluationStatus.COMPLETED:
            return jsonify({'error': 'Evaluation not completed'}), 400
        
        if not evaluation.report_file_s3_key:
            return jsonify({'error': 'No report file available'}), 404
        
        # Generate fresh download URL for local storage
        storage_service = LocalStorageService()
        
        # Get file content from local storage
        try:
            file_content = storage_service.get_file_content(evaluation.report_file_s3_key)
            
            flask_response = Response(
                file_content,
                mimetype='application/pdf',
                headers={
                    'Content-Disposition': f'attachment; filename="evaluation_{evaluation_id}.pdf"',
                    'Content-Length': str(len(file_content)),
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0'
                }
            )
            
            return flask_response
            
        except Exception as e:
            logger.error(f"Failed to get file content from local storage: {e}")
            return jsonify({'error': 'File not found in local storage'}), 404
            
    except Exception as e:
        logger.error(f"Error in direct download: {e}")
        return jsonify({'error': 'Download failed'}), 500

@upload_bp.route('/evaluations', methods=['GET'])
@jwt_required()
def get_user_evaluations():
    """Get all evaluations for current user"""
    try:
        current_user_id = get_jwt_identity()
        
        evaluations = Evaluation.query.filter_by(
            user_id=current_user_id
        ).order_by(Evaluation.created_at.desc()).all()
        
        return jsonify({
            'evaluations': [eval.to_dict() for eval in evaluations]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user evaluations: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Legacy endpoint for backward compatibility
@upload_bp.route('/basic-evaluate', methods=['POST'])
def basic_evaluate():
    """
    Basic evaluation endpoint for simple requirements
    Upload, evaluate, and return download URL in one step
    """
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if file was selected
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only .pdf and .docx files are allowed'}), 400
        
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
        
        # Save file temporarily first
        upload_folder = Config.UPLOAD_FOLDER
        os.makedirs(upload_folder, exist_ok=True)
        temp_file_path = os.path.join(upload_folder, unique_filename)
        
        try:
            file.save(temp_file_path)
            logger.info(f"File saved temporarily: {temp_file_path}")
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            return jsonify({'error': 'Failed to save uploaded file'}), 500
        
        # Upload original file to local storage using LocalStorageService
        storage_service = LocalStorageService()
        original_file_key = f"original_files/{unique_filename}"
        
        try:
            storage_service.upload_file(temp_file_path, original_file_key)
            logger.info(f"Original file uploaded to local storage: {original_file_key}")
        except Exception as e:
            logger.error(f"Failed to upload original file to local storage: {e}")
            # Continue with temporary file if local storage upload fails
        
        try:
            # Extract text content based on file type
            text_content = ""
            
            if file_extension == 'pdf':
                pdf_parser = PDFParser()
                parse_result = pdf_parser.parse_pdf_file(temp_file_path)
                text_content = parse_result['text_content']
            elif file_extension == 'docx':
                docx_parser = DOCXParser()
                parse_result = docx_parser.parse_docx_file(temp_file_path)
                text_content = parse_result['text_content']
            
            # Check if we got any text content
            if not text_content or len(text_content.strip()) < 50:
                return jsonify({
                    'error': 'Unable to extract text from document. Please ensure the document contains readable text.'
                }), 400
            
            # Evaluate with GPT
            gpt_evaluator = GPTEvaluator()
            evaluation_results = gpt_evaluator.evaluate_manuscript(text_content)
            
            # Generate PDF report
            pdf_generator = PDFGenerator()
            report_filename = f"evaluation_report_{uuid.uuid4().hex}.pdf"
            report_path = os.path.join(upload_folder, report_filename)
            
            metadata = {
                'original_filename': original_filename,
                'file_type': file_extension,
                'evaluation_date': datetime.now().isoformat()
            }
            
            pdf_generator.generate_evaluation_report(evaluation_results, metadata, report_path)
            
            # Upload to local storage
            download_url = None
            storage_service = LocalStorageService()
            try:
                file_key = f"reports/{report_filename}"
                storage_service.upload_file(report_path, file_key)
                download_url = storage_service.generate_download_url(file_key, expiration_hours=1)
                logger.info("Basic evaluation report uploaded to local storage successfully")
            except Exception as e:
                logger.error(f"Failed to upload to local storage: {e}")
                # Fall back to local URL
                download_url = f"/api/upload/public/download-file/reports/{report_filename}"
            
            # Clean up temporary files
            try:
                os.remove(temp_file_path)
                if os.path.exists(report_path):
                    os.remove(report_path)
            except Exception as e:
                logger.warning(f"Failed to clean up temporary files: {e}")
            
            return jsonify({
                'success': True,
                'download_url': download_url,
                'results': evaluation_results
            }), 200
            
        except Exception as e:
            logger.error(f"Error during evaluation: {e}")
            
            # Clean up temporary file
            try:
                os.remove(temp_file_path)
            except:
                pass
            
            return jsonify({
                'error': 'Evaluation failed',
                'message': str(e)
            }), 500
            
    except Exception as e:
        logger.error(f"Unexpected error in basic_evaluate: {e}")
        return jsonify({'error': 'Internal server error'}), 500 

@upload_bp.route('/evaluate-with-template', methods=['POST'])
@jwt_required()
def evaluate_with_template():
    """
    Evaluate document using custom template prompts
    """
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if files were uploaded
        if 'manuscript' not in request.files:
            return jsonify({'error': 'No manuscript file provided'}), 400
        
        if 'template' not in request.files:
            return jsonify({'error': 'No template file provided'}), 400
        
        manuscript_file = request.files['manuscript']
        template_file = request.files['template']
        
        # Check if files were selected
        if manuscript_file.filename == '':
            return jsonify({'error': 'No manuscript file selected'}), 400
        
        if template_file.filename == '':
            return jsonify({'error': 'No template file selected'}), 400
        
        # Validate file types
        manuscript_ext = manuscript_file.filename.rsplit('.', 1)[1].lower()
        template_ext = template_file.filename.rsplit('.', 1)[1].lower()
        
        if manuscript_ext not in ['pdf', 'docx']:
            return jsonify({'error': 'Invalid manuscript file type. Only .pdf and .docx files are allowed'}), 400
        
        if template_ext not in ['xls', 'xlsx']:
            return jsonify({'error': 'Invalid template file type. Only .xls and .xlsx files are allowed'}), 400
        
        # Generate unique filenames
        manuscript_filename = secure_filename(manuscript_file.filename)
        template_filename = secure_filename(template_file.filename)
        
        manuscript_unique = f"{uuid.uuid4().hex}.{manuscript_ext}"
        template_unique = f"template_{uuid.uuid4().hex}.{template_ext}"
        
        # Save files temporarily first
        upload_folder = Config.UPLOAD_FOLDER
        os.makedirs(upload_folder, exist_ok=True)
        
        manuscript_path = os.path.join(upload_folder, manuscript_unique)
        template_path = os.path.join(upload_folder, template_unique)
        
        try:
            manuscript_file.save(manuscript_path)
            template_file.save(template_path)
            logger.info(f"Files saved temporarily: {manuscript_path}, {template_path}")
        except Exception as e:
            logger.error(f"Error saving files: {e}")
            return jsonify({'error': 'Failed to save uploaded files'}), 500
        
        # Upload files to local storage using LocalStorageService
        storage_service = LocalStorageService()
        manuscript_file_key = f"original_files/{manuscript_unique}"
        template_file_key = f"templates/{template_unique}"
        
        try:
            storage_service.upload_file(manuscript_path, manuscript_file_key)
            storage_service.upload_file(template_path, template_file_key)
            logger.info(f"Files uploaded to local storage: {manuscript_file_key}, {template_file_key}")
        except Exception as e:
            logger.error(f"Failed to upload files to local storage: {e}")
            # Continue with temporary files if local storage upload fails
        
        # Create evaluation record
        evaluation = Evaluation(
            user_id=current_user_id,
            original_filename=manuscript_filename,
            original_file_s3_key=manuscript_file_key,
            status=EvaluationStatus.PROCESSING,
            file_size=os.path.getsize(manuscript_path),
            expires_at=datetime.utcnow() + timedelta(hours=Config.REPORT_EXPIRY_HOURS)
        )
        
        db.session.add(evaluation)
        db.session.commit()
        
        try:
            # Parse template file first
            template_evaluator = TemplateEvaluator()
            template_result = template_evaluator.parse_template_file(template_path)
            template_prompts = template_result['prompts']
            
            logger.info(f"Template parsed successfully with {len(template_prompts)} prompts")
            
            # Extract text content from manuscript
            text_content = ""
            
            if manuscript_ext == 'pdf':
                pdf_parser = PDFParser()
                parse_result = pdf_parser.parse_pdf_file(manuscript_path)
                text_content = parse_result['text_content']
            elif manuscript_ext == 'docx':
                docx_parser = DOCXParser()
                parse_result = docx_parser.parse_docx_file(manuscript_path)
                text_content = parse_result['text_content']
            
            # Check if we got any text content
            if not text_content or len(text_content.strip()) < 50:
                evaluation.status = EvaluationStatus.FAILED
                evaluation.error_message = 'Unable to extract text from manuscript. Please ensure the document contains readable text.'
                db.session.commit()
                return jsonify({
                    'error': 'Unable to extract text from manuscript. Please ensure the document contains readable text.'
                }), 400
            
            evaluation.text_length = len(text_content)
            
            # Evaluate with template prompts
            try:
                evaluation_results = template_evaluator.evaluate_with_template(text_content, template_prompts)
                if not evaluation_results or 'categories' not in evaluation_results:
                    raise Exception("Invalid evaluation results received")
            except Exception as eval_error:
                logger.error(f"Template evaluation failed: {eval_error}")
                evaluation.status = EvaluationStatus.FAILED
                evaluation.error_message = f'Template evaluation failed: {str(eval_error)}'
                db.session.commit()
                return jsonify({
                    'error': f'Template evaluation failed: {str(eval_error)}'
                }), 500
            
            # Update evaluation with results
            evaluation.evaluation_results = evaluation_results
            evaluation.evaluated_at = datetime.utcnow()
            
            # Extract individual scores
            categories = evaluation_results.get('categories', {})
            evaluation.line_editing_score = categories.get('line-editing', {}).get('score')
            evaluation.plot_score = categories.get('plot', {}).get('score')
            evaluation.character_score = categories.get('character', {}).get('score')
            evaluation.flow_score = categories.get('flow', {}).get('score')
            evaluation.worldbuilding_score = categories.get('worldbuilding', {}).get('score')
            evaluation.readiness_score = categories.get('readiness', {}).get('score')
            
            # Calculate overall score
            evaluation.calculate_overall_score()
            
            # Generate PDF report
            pdf_generator = PDFGenerator()
            report_filename = f"template_evaluation_report_{evaluation.id}_{uuid.uuid4().hex}.pdf"
            report_path = os.path.join(upload_folder, report_filename)
            
            metadata = {
                'original_filename': manuscript_filename,
                'template_filename': template_filename,
                'file_type': manuscript_ext,
                'evaluation_date': datetime.now().isoformat(),
                'evaluation_id': evaluation.id,
                'template_used': True
            }
            
            pdf_generator.generate_evaluation_report(evaluation_results, metadata, report_path)
            
            # Upload report to local storage
            download_url = None
            storage_service = LocalStorageService()
            try:
                file_key = f"reports/{report_filename}"
                storage_service.upload_file(report_path, file_key)
                download_url = storage_service.generate_download_url(file_key, expiration_hours=1)  # 1 hour
                evaluation.report_file_s3_key = file_key
                evaluation.download_url = download_url
                logger.info("Template report uploaded to local storage successfully")
            except Exception as e:
                logger.error(f"Failed to upload template report to local storage: {e}")
                # Fall back to direct file path
                evaluation.report_file_s3_key = f"reports/{report_filename}"
                evaluation.download_url = f"/api/upload/public/download-file/reports/{report_filename}"
            
            # Mark evaluation as completed
            evaluation.status = EvaluationStatus.COMPLETED
            db.session.commit()
            
            # Clean up temporary files
            try:
                os.remove(manuscript_path)
                os.remove(template_path)
                if os.path.exists(report_path):
                    os.remove(report_path)
            except Exception as e:
                logger.warning(f"Failed to clean up temporary files: {e}")
            
            # Return success response
            return jsonify({
                'success': True,
                'evaluation_id': evaluation.id,
                'message': 'Template-based document evaluation completed successfully',
                'download_url': download_url,
                'results': evaluation_results,
                'template_info': {
                    'filename': template_filename,
                    'prompts_found': len(template_prompts),
                    'categories': list(template_prompts.keys())
                }
            }), 200
            
        except Exception as e:
            logger.error(f"Error during template evaluation: {e}")
            evaluation.status = EvaluationStatus.FAILED
            evaluation.error_message = str(e)
            db.session.commit()
            
            # Clean up temporary files
            try:
                os.remove(manuscript_path)
                os.remove(template_path)
            except:
                pass
            
            return jsonify({
                'error': f'Template evaluation failed: {str(e)}'
            }), 500
        
    except Exception as e:
        logger.error(f"Template evaluation endpoint error: {e}")
        return jsonify({'error': 'Internal server error'}), 500 

def perform_multi_method_evaluation(text_content, evaluation_methods, selected_templates, user_id):
    """
    Perform evaluation using multiple methods and templates
    """
    import threading
    import time
    from app.services.gpt_evaluator import GPTEvaluator
    from app.services.template_evaluator import TemplateEvaluator
    from app.models.evaluation import EvaluationTemplate
    
    # Cross-platform timeout implementation
    timeout_occurred = False
    
    def timeout_handler():
        nonlocal timeout_occurred
        timeout_occurred = True
    
    # Set timeout for the entire evaluation process (8 minutes)
    timer = threading.Timer(480, timeout_handler)  # 8 minutes timeout
    timer.start()
    
    try:
        logger.info(f"Starting multi-method evaluation for user {user_id}")
        logger.info(f"Methods: {evaluation_methods}, Templates: {selected_templates}")
        
        gpt_evaluator = GPTEvaluator()
        template_evaluator = TemplateEvaluator()
    
        all_results = {}
        combined_categories = {}
    
        # Process each evaluation method
        for method in evaluation_methods:
            # Check for timeout
            if timeout_occurred:
                raise TimeoutError("Evaluation timeout - process took too long")
                
            if method == 'basic':
                # Use default GPT evaluation
                try:
                    basic_results = gpt_evaluator.evaluate_manuscript(text_content)
                    all_results['basic'] = basic_results
                    
                    # Merge categories
                    categories = basic_results.get('categories', {})
                    for category_id, category_data in categories.items():
                        if category_id not in combined_categories:
                            combined_categories[category_id] = category_data
                        else:
                            # Average scores if multiple methods evaluate same category
                            existing_score = combined_categories[category_id].get('score', 0)
                            new_score = category_data.get('score', 0)
                            combined_categories[category_id]['score'] = round((existing_score + new_score) / 2)
                            
                except Exception as e:
                    logger.error(f"Basic evaluation failed: {e}")
                    continue
                    
            elif method == 'template' and selected_templates:
                # Use selected templates
                for template_id in selected_templates:
                    # Check for timeout
                    if timeout_occurred:
                        raise TimeoutError("Evaluation timeout - process took too long")
                        
                    try:
                        template = EvaluationTemplate.query.filter_by(
                            id=template_id,
                            uploaded_by=user_id,
                            is_active=True
                        ).first()
                        
                        if template:
                            # Get template file and parse it
                            from app.services.local_storage_service import LocalStorageService
                            storage_service = LocalStorageService()
                            template_content = storage_service.get_file_content(template.file_s3_key)
                            
                            # Save template temporarily
                            temp_template_path = os.path.join(Config.UPLOAD_FOLDER, f'temp_template_{template_id}.xlsx')
                            with open(temp_template_path, 'wb') as f:
                                f.write(template_content)
                            
                            try:
                                # Parse template and evaluate
                                template_data = template_evaluator.parse_template_file(temp_template_path)
                                template_prompts = template_data.get('prompts', {})
                                
                                if template_prompts:
                                    template_results = template_evaluator.evaluate_with_template(text_content, template_prompts)
                                    all_results[f'template_{template_id}'] = template_results
                                    
                                    # Merge categories
                                    categories = template_results.get('categories', {})
                                    for category_id, category_data in categories.items():
                                        if category_id not in combined_categories:
                                            combined_categories[category_id] = category_data
                                        else:
                                            # Average scores
                                            existing_score = combined_categories[category_id].get('score', 0)
                                            new_score = category_data.get('score', 0)
                                            combined_categories[category_id]['score'] = round((existing_score + new_score) / 2)
                            
                            finally:
                                # Clean up temp file
                                if os.path.exists(temp_template_path):
                                    os.remove(temp_template_path)
                                    
                    except Exception as e:
                        logger.error(f"Template evaluation failed for template {template_id}: {e}")
                        continue
        
        # Check for timeout before returning results
        if timeout_occurred:
            raise TimeoutError("Evaluation timeout - process took too long")
        
        # Calculate overall score from combined categories
        scores = [cat.get('score', 0) for cat in combined_categories.values()]
        overall_score = round(sum(scores) / len(scores)) if scores else 0
        
        logger.info(f"Evaluation completed successfully for user {user_id}")
        
        return {
            'categories': combined_categories,
            'overall_score': overall_score,
            'evaluation_date': datetime.now().isoformat(),
            'methods_used': evaluation_methods,
            'templates_used': selected_templates,
            'all_results': all_results
        }
        
    except TimeoutError as e:
        logger.error(f"Evaluation timeout for user {user_id}: {e}")
        raise e
    except Exception as e:
        logger.error(f"Evaluation failed for user {user_id}: {e}")
        raise e
    finally:
        # Cancel the timer
        timer.cancel() 