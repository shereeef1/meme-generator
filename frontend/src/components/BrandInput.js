import React, { useState, useEffect } from 'react';
import { scrapeBrandData, getDocuments, deleteDocument, updateDocument } from '../api';

const CATEGORIES = [
  { value: '', label: 'Select a category (optional)' },
  { value: 'fashion', label: 'Fashion & Apparel' },
  { value: 'beauty', label: 'Beauty & Cosmetics' },
  { value: 'tech', label: 'Technology & Electronics' },
  { value: 'food', label: 'Food & Beverage' },
  { value: 'health', label: 'Health & Wellness' },
  { value: 'home', label: 'Home & Decor' },
  { value: 'other', label: 'Other' }
];

const COUNTRIES = [
  { value: '', label: 'Select a country (optional)' },
  { value: 'us', label: 'United States' },
  { value: 'uk', label: 'United Kingdom' },
  { value: 'ca', label: 'Canada' },
  { value: 'au', label: 'Australia' },
  { value: 'de', label: 'Germany' },
  { value: 'fr', label: 'France' },
  { value: 'jp', label: 'Japan' },
  { value: 'in', label: 'India' },
  { value: 'br', label: 'Brazil' },
  { value: 'other', label: 'Other' }
];

const BrandInput = ({ onBrandData }) => {
  const [inputMethod, setInputMethod] = useState('scrape');
  const [url, setUrl] = useState('');
  const [category, setCategory] = useState('');
  const [country, setCountry] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [brandData, setBrandData] = useState(null);
  const [isTextConfirmed, setIsTextConfirmed] = useState(false);
  const [showRawText, setShowRawText] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [editContent, setEditContent] = useState('');
  const [fileInputKey, setFileInputKey] = useState(Date.now());
  const [status, setStatus] = useState('');

  const resetForm = () => {
    setUrl('');
    setCategory('');
    setCountry('');
    setUploadedFile(null);
    setError(null);
    setBrandData(null);
    setIsTextConfirmed(false);
    setShowRawText(false);
    setFileInputKey(Date.now());
  };

  useEffect(() => {
    resetForm();
  }, [inputMethod]);

  useEffect(() => {
    if (selectedDocument) {
      setEditContent(selectedDocument.content || '');
      setEditMode(false);
    } else {
      setEditContent('');
      setEditMode(false);
    }
  }, [selectedDocument]);

  useEffect(() => {
    loadDocuments();
  }, [currentPage]);

  const loadDocuments = async () => {
    try {
      const response = await getDocuments(currentPage);
      if (response.success) {
        setDocuments(response.documents);
        setTotalPages(Math.ceil(response.total / response.per_page));
      }
    } catch (err) {
      console.error('Error loading documents:', err);
      setError('Failed to load document history');
    }
  };

  const handleDeleteDocument = async (docId) => {
    if (window.confirm('Are you sure you want to delete this document?')) {
      try {
        const response = await deleteDocument(docId);
        if (response.success) {
          await loadDocuments();
          setSelectedDocument(null);
        } else {
          setError('Failed to delete document');
        }
      } catch (err) {
        console.error('Error deleting document:', err);
        setError('Failed to delete document');
      }
    }
  };

  const handleUpdateDocument = async () => {
    try {
      const response = await updateDocument(selectedDocument.id, editContent);
      if (response.success) {
        setEditMode(false);
        await loadDocuments();
        setSelectedDocument(null);
      } else {
        setError('Failed to update document');
      }
    } catch (err) {
      console.error('Error updating document:', err);
      setError('Failed to update document');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (isTextConfirmed) {
      onBrandData(brandData);
      return;
    }
    
    if (!inputMethod || (inputMethod === 'scrape' && !url) || (inputMethod === 'upload' && !uploadedFile)) {
      setError('Please provide a URL or upload a file');
      return;
    }
    
    setLoading(true);
    setError(null);
    setBrandData(null);
    setShowRawText(false);
    setIsTextConfirmed(false);
    
    try {
      if (inputMethod === 'scrape') {
        let formattedUrl = url;
        if (!url.startsWith('http://') && !url.startsWith('https://')) {
          formattedUrl = `https://${url}`;
        }
        
        console.log(`BrandInput - Scraping data from: ${formattedUrl}`);
        setError(null);
        setLoading(true);
        
        // Show immediate feedback to the user that scraping has started
        setStatus('Scraping website data. This may take up to 30-60 seconds for larger sites...');
        
        const data = await scrapeBrandData(formattedUrl, category || undefined, country || undefined);
        
        if (data.success) {
          console.log(`BrandInput - Scraping successful, raw_text length: ${data.raw_text ? data.raw_text.length : 'none'}`);
          setStatus('');
          
          if (!data.raw_text || data.raw_text.trim() === '') {
            console.error('BrandInput - Warning: Scraped data has empty raw_text!');
            // Provide a basic default
            data.raw_text = `Data scraped from ${formattedUrl}\nBrand: ${data.brand_name || url}`;
          }
          
          // If we're using fallback data, let the user know
          if (data.scrape_quality === 'fallback' || data.scrape_quality === 'minimal') {
            setStatus(`Limited data was retrieved from this website due to access restrictions. We've provided what we could find, but you may want to try uploading a file for better results.`);
          }
          
          setBrandData(data);
          setShowRawText(true);
        } else {
          console.error('BrandInput - Scraping failed:', data.error || 'Unknown error');
          setStatus('');
          setError(data.message || 'Failed to scrape brand data. Please try uploading a file instead.');
        }
      } else {
        const reader = new FileReader();
        reader.onload = async (e) => {
          const text = e.target.result;
          console.log(`BrandInput - File read successful, content length: ${text ? text.length : 'none'}`);
          
          if (!text || text.trim() === '') {
            console.error('BrandInput - Warning: Uploaded file has empty content!');
            setError('The uploaded file appears to be empty. Please try a different file.');
            setLoading(false);
            return;
          }
          
          const data = {
            success: true,
            brand_name: uploadedFile.name.replace(/\.[^/.]+$/, ""),
            raw_text: text,
            source_url: 'File Upload',
            category: category || undefined,
            country: country || undefined
          };
          setBrandData(data);
          setShowRawText(true);
        };
        reader.onerror = () => {
          setError('Error reading the uploaded file');
        };
        reader.readAsText(uploadedFile);
      }
    } catch (err) {
      console.error('Error processing brand data:', err);
      setStatus('');
      
      // Provide more specific error guidance
      if (err.message && err.message.includes('network')) {
        setError('Network error when connecting to the server. Please check your internet connection or try uploading a file instead.');
      } else if (err.message && err.message.includes('timeout')) {
        setError('The operation timed out. This website may be too large or complex to scrape. Please try uploading a file instead.');
      } else {
        setError('An error occurred while processing the data. Please try again or upload a file instead.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.type === 'text/plain' || file.type === 'application/msword' || 
          file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
        setUploadedFile(file);
        setError(null);
        
        // Read file content as text
        const reader = new FileReader();
        reader.onload = async (e) => {
          const text = e.target.result;
          const data = {
            success: true,
            brand_name: file.name.replace(/\.[^/.]+$/, ""),
            raw_text: text,
            source_url: 'File Upload',
            category: category || undefined,
            country: country || undefined
          };
          setBrandData(data);
          setShowRawText(true);
        };
        reader.onerror = () => {
          setError('Error reading the uploaded file');
          setUploadedFile(null);
        };
        
        // Read as text for all file types
        reader.readAsText(file);
      } else {
        setError('Please upload a .txt or .doc/.docx file');
        e.target.value = '';
        setUploadedFile(null);
      }
    } else {
      setUploadedFile(null);
    }
  };

  const handleConfirmText = () => {
    setIsTextConfirmed(true);
    if (onBrandData && typeof onBrandData === 'function') {
      console.log('BrandInput - Sending brand data with raw_text:', 
        brandData.raw_text ? 
        `${brandData.raw_text.substring(0, 100)}... (${brandData.raw_text.length} chars)` : 
        'No raw_text');
      onBrandData(brandData);
    }
  };

  const downloadRawText = () => {
    const blob = new Blob([brandData.raw_text], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${brandData.brand_name.toLowerCase().replace(/\s+/g, '-')}-content.txt`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  return (
    <div className="card mb-4">
      <div className="card-header bg-primary text-white">
        <h2 className="h5 mb-0">Brand Information</h2>
      </div>
      <div className="card-body">
        {/* Show error message if any */}
        {error && (
          <div className="alert alert-danger" role="alert">
            {error}
            {error.includes('scrape') && (
              <div className="mt-2">
                <button 
                  className="btn btn-sm btn-outline-primary" 
                  onClick={() => setInputMethod('upload')}
                >
                  Switch to File Upload
                </button>
              </div>
            )}
          </div>
        )}
        
        {/* Show status message during operations */}
        {status && !error && (
          <div className="alert alert-info" role="alert">
            <div className="d-flex align-items-center">
              <div className="spinner-border spinner-border-sm me-2" role="status">
                <span className="visually-hidden">Loading...</span>
              </div>
              <span>{status}</span>
            </div>
          </div>
        )}
        
        <ul className="nav nav-tabs mb-4">
          <li className="nav-item">
            <button 
              className={`nav-link ${!selectedDocument ? 'active' : ''}`}
              onClick={() => setSelectedDocument(null)}
            >
              New Document
            </button>
          </li>
          <li className="nav-item">
            <button 
              className={`nav-link ${selectedDocument ? 'active' : ''}`}
              onClick={() => loadDocuments()}
            >
              Document History
            </button>
          </li>
        </ul>

        {!selectedDocument ? (
          <>
            <div className="mb-4">
              <div className="btn-group w-100" role="group">
                <input
                  type="radio"
                  className="btn-check"
                  name="inputMethod"
                  id="scrapeMethod"
                  checked={inputMethod === 'scrape'}
                  onChange={() => setInputMethod('scrape')}
                />
                <label className="btn btn-outline-primary" htmlFor="scrapeMethod">
                  <i className="bi bi-globe me-2"></i>
                  Scrape Website
                </label>

                <input
                  type="radio"
                  className="btn-check"
                  name="inputMethod"
                  id="uploadMethod"
                  checked={inputMethod === 'upload'}
                  onChange={() => setInputMethod('upload')}
                />
                <label className="btn btn-outline-primary" htmlFor="uploadMethod">
                  <i className="bi bi-file-earmark-text me-2"></i>
                  Upload File
                </label>
              </div>
            </div>

            <form onSubmit={handleSubmit}>
              {inputMethod === 'scrape' ? (
                <div className="mb-3">
                  <label htmlFor="brandUrl" className="form-label">
                    Enter Brand Website URL
                  </label>
                  <input
                    type="text"
                    id="brandUrl"
                    className="form-control"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="e.g., nike.com or https://www.apple.com"
                    required={inputMethod === 'scrape'}
                  />
                  <div className="form-text">
                    We'll scrape the website content for analysis.
                  </div>
                </div>
              ) : (
                <div className="mb-3">
                  <label htmlFor="fileUpload" className="form-label">
                    Upload Brand Information File
                  </label>
                  <input
                    type="file"
                    id="fileUpload"
                    key={fileInputKey}
                    className="form-control"
                    onChange={handleFileUpload}
                    accept=".txt,.doc,.docx"
                    required={inputMethod === 'upload'}
                  />
                  <div className="form-text">
                    Upload a text or Word document containing your brand information.
                  </div>
                </div>
              )}
              
              <div className="row">
                <div className="col-md-6 mb-3">
                  <label htmlFor="category" className="form-label">
                    Brand Category
                  </label>
                  <select
                    id="category"
                    className="form-select"
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                  >
                    {CATEGORIES.map(option => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div className="col-md-6 mb-3">
                  <label htmlFor="country" className="form-label">
                    Primary Market
                  </label>
                  <select
                    id="country"
                    className="form-select"
                    value={country}
                    onChange={(e) => setCountry(e.target.value)}
                  >
                    {COUNTRIES.map(option => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              
              <button
                type="submit"
                className="btn btn-primary"
                disabled={loading || (inputMethod === 'scrape' && !url.trim()) || (inputMethod === 'upload' && !uploadedFile)}
              >
                {loading ? (
                  <span>
                    <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                    {inputMethod === 'scrape' ? 'Scraping Website...' : 'Processing File...'}
                  </span>
                ) : (
                  inputMethod === 'scrape' ? 'Get Brand Data' : 'Process File'
                )}
              </button>
            </form>
          </>
        ) : (
          <div className="document-history">
            <div className="row">
              <div className="col-md-4">
                <div className="list-group">
                  {documents.map(doc => (
                    <button
                      key={doc.id}
                      className={`list-group-item list-group-item-action ${selectedDocument?.id === doc.id ? 'active' : ''}`}
                      onClick={() => setSelectedDocument(doc)}
                    >
                      <div className="d-flex w-100 justify-content-between">
                        <h6 className="mb-1">{doc.filename}</h6>
                        <small>{new Date(doc.created_at).toLocaleDateString()}</small>
                      </div>
                      <p className="mb-1">{doc.category || 'No category'}</p>
                      <small>{doc.country || 'No country specified'}</small>
                    </button>
                  ))}
                </div>
                
                {totalPages > 1 && (
                  <div className="d-flex justify-content-center mt-3">
                    <nav>
                      <ul className="pagination">
                        <li className={`page-item ${currentPage === 1 ? 'disabled' : ''}`}>
                          <button
                            className="page-link"
                            onClick={() => setCurrentPage(prev => prev - 1)}
                            disabled={currentPage === 1}
                          >
                            Previous
                          </button>
                        </li>
                        <li className={`page-item ${currentPage === totalPages ? 'disabled' : ''}`}>
                          <button
                            className="page-link"
                            onClick={() => setCurrentPage(prev => prev + 1)}
                            disabled={currentPage === totalPages}
                          >
                            Next
                          </button>
                        </li>
                      </ul>
                    </nav>
                  </div>
                )}
              </div>
              
              <div className="col-md-8">
                {selectedDocument && (
                  <div className="card">
                    <div className="card-header d-flex justify-content-between align-items-center">
                      <h5 className="mb-0">Document Details</h5>
                      <div>
                        <button
                          className="btn btn-sm btn-outline-primary me-2"
                          onClick={() => {
                            setEditMode(!editMode);
                            setEditContent(selectedDocument.content);
                          }}
                        >
                          {editMode ? 'Cancel Edit' : 'Edit'}
                        </button>
                        <button
                          className="btn btn-sm btn-outline-danger"
                          onClick={() => handleDeleteDocument(selectedDocument.id)}
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                    <div className="card-body">
                      {editMode ? (
                        <>
                          <textarea
                            className="form-control mb-3"
                            rows="10"
                            value={editContent}
                            onChange={(e) => setEditContent(e.target.value)}
                          />
                          <button
                            className="btn btn-primary"
                            onClick={handleUpdateDocument}
                          >
                            Save Changes
                          </button>
                        </>
                      ) : (
                        <>
                          <p><strong>Source:</strong> {selectedDocument.source_url}</p>
                          <p><strong>Category:</strong> {selectedDocument.category || 'Not specified'}</p>
                          <p><strong>Country:</strong> {selectedDocument.country || 'Not specified'}</p>
                          <p><strong>Created:</strong> {new Date(selectedDocument.created_at).toLocaleString()}</p>
                          <hr />
                          <div className="document-content">
                            <pre className="bg-light p-3 rounded">
                              {selectedDocument.content}
                            </pre>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {brandData && !isTextConfirmed && (
          <div className="mt-4">
            <div className="card">
              <div className="card-header">
                <h5 className="mb-0">Review Content</h5>
              </div>
              <div className="card-body">
                <div className="mb-3">
                  <button
                    className="btn btn-link p-0"
                    onClick={() => setShowRawText(!showRawText)}
                  >
                    {showRawText ? 'Hide Raw Text' : 'Show Raw Text'}
                  </button>
                </div>
                
                {showRawText && (
                  <div className="mb-3">
                    <div className="bg-light p-3 rounded" style={{ maxHeight: '300px', overflow: 'auto' }}>
                      <pre className="mb-0">{brandData.raw_text}</pre>
                    </div>
                    <button
                      className="btn btn-sm btn-outline-secondary mt-2"
                      onClick={downloadRawText}
                    >
                      Download Raw Text
                    </button>
                  </div>
                )}
                
                <div className="d-flex justify-content-end">
                  <button
                    className="btn btn-primary"
                    onClick={handleConfirmText}
                    disabled={loading}
                  >
                    Confirm & Continue
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default BrandInput; 