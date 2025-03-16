import React, { useState, useEffect } from 'react';
import { scrapeBrandData, getDocuments, deleteDocument, updateDocument, enhancedBrandResearch, scrapeBrandWebsite, enhanced_research, searchDocuments, getDocument, llmDeepSearchBrand } from '../api';

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
  const [enhancedOptions, setEnhancedOptions] = useState({
    includeCompetitors: true,
    includeTrends: true,
    brandNameInput: ''
  });
  const [warning, setWarning] = useState(null);
  const [brandName, setBrandName] = useState('');

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
    setBrandName('');
  };

  useEffect(() => {
    resetForm();
    // Clear the brand name input when changing methods
    if (inputMethod === 'enhanced') {
      setEnhancedOptions({ ...enhancedOptions, brandNameInput: '' });
    }
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
    setLoading(true);
    setError(null);
    setStatus(null);
    
    try {
      if (inputMethod === 'scrape' && !url) {
        setError('Please provide a URL to scrape');
        setLoading(false);
        return;
      } else if (inputMethod === 'upload' && !uploadedFile) {
        setError('Please select a file to upload');
        setLoading(false);
        return;
      } else if (inputMethod === 'enhanced' && !enhancedOptions.brandNameInput) {
        setError('Please enter a brand name for enhanced research');
        setLoading(false);
        return;
      } else if (inputMethod === 'llm_deepsearch' && !brandName) {
        setError('Please enter a brand name for LLM DeepSearch');
        setLoading(false);
        return;
      }
      
      if (inputMethod === 'scrape') {
        let formattedUrl = url;
        
        // Add http:// prefix if missing
        if (!url.startsWith('http://') && !url.startsWith('https://')) {
          formattedUrl = `https://${url}`;
        }
        
        setStatus('Scraping website...');
        
        try {
          const data = await scrapeBrandData(formattedUrl);
          setBrandData(data);
          setShowRawText(true);
          setIsTextConfirmed(false); // Ensure this is set to false so confirmation is required
          
          // Don't call onBrandData here - wait for user confirmation
        } catch (err) {
          console.error('Error scraping website:', err);
          setError(`Error: ${err.message || 'Failed to connect to the server. Please try again.'}`);
        }
      } else if (inputMethod === 'upload') {
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
          setIsTextConfirmed(false); // Ensure this is set to false so confirmation is required
          
          // Don't call onBrandData here - wait for user confirmation
        };
        reader.onerror = () => {
          setError('Error reading the uploaded file');
        };
        reader.readAsText(uploadedFile);
      } else if (inputMethod === 'enhanced') {
        const brandName = enhancedOptions.brandNameInput;
        
        console.log(`BrandInput - Starting enhanced research for: ${brandName}`);
        setError(null);
        setLoading(true);
        
        setStatus('Performing enhanced brand research. This may take up to 1-2 minutes...');
        
        try {
          const data = await enhancedBrandResearch(
            brandName,
            category || undefined,
            country || undefined,
            {
              includeCompetitors: enhancedOptions.includeCompetitors,
              includeTrends: enhancedOptions.includeTrends
            }
          );
          
          if (data.success) {
            console.log(`BrandInput - Enhanced research successful, raw_text length: ${data.raw_text ? data.raw_text.length : 'none'}`);
            setStatus('');
            
            if (!data.raw_text || data.raw_text.trim() === '') {
              console.error('BrandInput - Warning: Enhanced research has empty raw_text!');
              data.raw_text = `Enhanced research for ${brandName}\nBrand: ${data.brand_name || brandName}`;
            }
            
            // Check if there were partial failures and add a warning
            if (data.partial_failures && data.partial_failures.length > 0) {
              const failedSources = data.partial_failures.map(f => f.source).join(', ');
              console.warn(`BrandInput - Enhanced research had partial failures: ${failedSources}`);
              
              // Add a warning to the UI
              setWarning(`Some data sources (${failedSources}) couldn't be accessed. Results may be incomplete.`);
              
              // If we have a warning message from the backend, use that
              if (data.warning) {
                setWarning(data.warning);
              }
            } else {
              setWarning(null);
            }
            
            setBrandData(data);
            setShowRawText(true);
            setIsTextConfirmed(false); // Ensure this is set to false so confirmation is required
            
            // Don't call onBrandData here - wait for user confirmation
          } else {
            console.error('BrandInput - Enhanced research failed:', data.error || 'Unknown error');
            setStatus('');
            
            // Provide more specific error messages based on the error type
            if (data.error && data.error.includes('rate limiting')) {
              setError('Search services are currently rate limited. Please try again in a few minutes or use a different method.');
            } else if (data.error && data.error.includes('All data sources failed')) {
              setError(`Couldn't find information for "${brandName}". Please check the spelling or try a different brand name.`);
            } else {
              setError(data.message || 'Failed to perform enhanced brand research. Please try another method.');
            }
          }
        } catch (err) {
          console.error('BrandInput - Error during enhanced research:', err);
          setStatus('');
          setError(`Error: ${err.message || 'Failed to connect to the server. Please try again.'}`);
        }
      } else if (inputMethod === 'llm_deepsearch') {
        if (!brandName) {
          setError('Please enter a brand name for LLM DeepSearch');
          setLoading(false);
          return;
        }
        
        setStatus('Performing deep LLM research on the brand...');
        console.log(`BrandInput - Starting LLM DeepSearch for: ${brandName}`);
        
        try {
          const data = await llmDeepSearchBrand(brandName, category, country);
          
          if (data.success) {
            // Log the data received
            console.log(`BrandInput - LLM DeepSearch successful, raw_text length: ${data.raw_text ? data.raw_text.length : 'none'}`);
            
            // Check if the raw_text is empty and log a warning
            if (!data.raw_text || data.raw_text.trim().length === 0) {
              console.error('BrandInput - Warning: LLM DeepSearch has empty raw_text!');
              data.raw_text = `LLM DeepSearch for ${brandName}\nBrand: ${data.brand_name || brandName}`;
              if (data.data && Object.keys(data.data).length > 0) {
                data.raw_text += '\n\nLimited information available from LLM DeepSearch.';
              }
            }
            
            setBrandData(data);
            setShowRawText(true);
            setIsTextConfirmed(false); // Ensure this is set to false so confirmation is required
            
            // Don't call onBrandData here - wait for user confirmation
          } else {
            console.error('BrandInput - LLM DeepSearch failed:', data.error || 'Unknown error');
            setError(data.message || 'Failed to get brand information. Please try a different brand name or try again later.');
          }
        } catch (err) {
          console.error('BrandInput - Error during LLM DeepSearch:', err);
          setError(err.message || 'Failed to perform LLM DeepSearch. Please try again later.');
        }
      }
    } catch (err) {
      console.error('Error processing brand data:', err);
      setStatus('');
      
      if (err.message && err.message.includes('network')) {
        setError('Network error when connecting to the server. Please check your internet connection or try uploading a file instead.');
      } else if (err.message && err.message.includes('timeout')) {
        setError('The operation timed out. Please try again with a more specific brand name or try a different approach.');
      } else {
        setError(`Error: ${err.message || 'An unknown error occurred. Please try again.'}`);
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
          setIsTextConfirmed(false); // Ensure this is set to false so confirmation is required
          
          // Don't call onBrandData here - wait for user confirmation
        };
        reader.onerror = () => {
          setError('Error reading the uploaded file');
          setUploadedFile(null);
        };
        
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
    // Call onBrandData here to pass the data to the next step
    if (onBrandData && typeof onBrandData === 'function' && brandData) {
      console.log('BrandInput - Sending brand data after confirmation with raw_text:', 
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
                
                <input
                  type="radio"
                  className="btn-check"
                  name="inputMethod"
                  id="enhancedMethod"
                  checked={inputMethod === 'enhanced'}
                  onChange={() => setInputMethod('enhanced')}
                />
                <label className="btn btn-outline-primary" htmlFor="enhancedMethod">
                  <i className="bi bi-search me-2"></i>
                  Enhanced Research
                </label>
                
                <input
                  type="radio"
                  className="btn-check"
                  name="inputMethod"
                  id="llmDeepsearchMethod"
                  checked={inputMethod === 'llm_deepsearch'}
                  onChange={() => setInputMethod('llm_deepsearch')}
                />
                <label className="btn btn-outline-primary" htmlFor="llmDeepsearchMethod">
                  <i className="bi bi-robot me-2"></i>
                  LLM DeepSearch
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
              ) : inputMethod === 'upload' ? (
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
              ) : inputMethod === 'enhanced' || inputMethod === 'llm_deepsearch' ? (
                <>
                  <div className="mb-3">
                    <label htmlFor="brandName" className="form-label">
                      Brand Name
                    </label>
                    <input
                      type="text"
                      id="brandName"
                      className="form-control"
                      value={brandName}
                      onChange={(e) => setBrandName(e.target.value)}
                      placeholder="e.g., Nike, Apple, Tesla"
                      required
                    />
                    <div className="form-text">
                      {inputMethod === 'enhanced' ? 
                        "We'll research this brand from multiple online sources." :
                        "We'll use our AI to gather comprehensive information about this brand."}
                    </div>
                  </div>

                  <div className="row">
                    <div className="col-md-6 mb-3">
                      <label htmlFor="category" className="form-label">
                        Category (Optional)
                      </label>
                      <input
                        type="text"
                        id="category"
                        className="form-control"
                        value={category}
                        onChange={(e) => setCategory(e.target.value)}
                        placeholder="e.g., Technology, Fashion"
                      />
                    </div>
                    <div className="col-md-6 mb-3">
                      <label htmlFor="country" className="form-label">
                        Country (Optional)
                      </label>
                      <input
                        type="text"
                        id="country"
                        className="form-control"
                        value={country}
                        onChange={(e) => setCountry(e.target.value)}
                        placeholder="e.g., US, India, UK"
                      />
                    </div>
                  </div>
                </>
              ) : null}

              <div className="d-grid gap-2">
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={loading}
                >
                  {loading ? (
                    <span>
                      <span className="spinner-border spinner-border-sm me-2" role="status"></span>
                      {status || 'Processing...'}
                    </span>
                  ) : (
                    <>
                      {inputMethod === 'scrape' ? (
                        <><i className="bi bi-globe me-2"></i>Get Brand Info</>
                      ) : inputMethod === 'upload' ? (
                        <><i className="bi bi-file-earmark-text me-2"></i>Process File</>
                      ) : inputMethod === 'enhanced' ? (
                        <><i className="bi bi-search me-2"></i>Start Enhanced Research</>
                      ) : inputMethod === 'llm_deepsearch' ? (
                        <><i className="bi bi-robot me-2"></i>Start LLM DeepSearch</>
                      ) : (
                        'Continue'
                      )}
                    </>
                  )}
                </button>
              </div>
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

        {warning && (
          <div className="mt-4">
            <div className="card">
              <div className="card-header">
                <h5 className="mb-0">Warning</h5>
              </div>
              <div className="card-body">
                <p>{warning}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default BrandInput; 