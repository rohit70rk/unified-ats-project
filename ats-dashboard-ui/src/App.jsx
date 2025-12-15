import { useState, useEffect } from 'react';
import { fetchJobs, createCandidate, fetchApplications, createJob } from './api';
import './App.css';

function App() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Modal State
  const [activeJob, setActiveJob] = useState(null);
  const [modalMode, setModalMode] = useState(null);

  // Data for Modals
  const [applications, setApplications] = useState([]);
  const [appLoading, setAppLoading] = useState(false);
  
  // UPDATED: Split Name State
  const [formData, setFormData] = useState({ 
    first_name: '', 
    last_name: '', 
    email: '', 
    phone: '', 
    resume_url: '' 
  });

  // UPDATED: New Job Fields (Remote, City, Country)
  const [jobFormData, setJobFormData] = useState({ 
    title: '', 
    city: '', 
    country: '', 
    description: '', 
    remote: false 
  });
  
  const [submitStatus, setSubmitStatus] = useState(null);

  useEffect(() => {
    loadJobs(); 
  }, []);

  const loadJobs = async () => {
    setLoading(true);
    try {
      const data = await fetchJobs();
      if (data && data.length > 0) {
        setJobs(data);
      } else {
        setJobs([]); 
      }
      setError(null);
    } catch (err) {
      console.error(err);
      setError("Could not connect to Unified ATS Service.");
    } finally {
      setLoading(false);
    }
  };

  const openApplyModal = (job) => {
    setActiveJob(job);
    setModalMode('APPLY');
    // Reset form with split names
    setFormData({ 
      first_name: '', 
      last_name: '', 
      email: '', 
      phone: '', 
      resume_url: 'https://linkedin.com/in/example' 
    });
    setSubmitStatus(null);
  };

  const openViewAppsModal = async (job) => {
    setActiveJob(job);
    setModalMode('VIEW_APPS');
    setAppLoading(true);
    setApplications([]);
    try {
      const apps = await fetchApplications(job.id);
      setApplications(apps);
    } catch (err) {
      alert("Failed to fetch applications.");
    } finally {
      setAppLoading(false);
    }
  };

  const openDescriptionModal = (job) => {
    setActiveJob(job);
    setModalMode('VIEW_DESC');
  };

  const openCreateJobModal = () => {
    setModalMode('CREATE_JOB');
    // Reset form with new fields
    setJobFormData({ title: '', city: '', country: '', description: '', remote: false });
    setSubmitStatus(null);
  };

  const closeModal = () => {
    setModalMode(null);
    setActiveJob(null);
  };

  const handleApplySubmit = async (e) => {
    e.preventDefault();
    setSubmitStatus('sending');
    try {
      await createCandidate({ ...formData, job_id: activeJob.id });
      setSubmitStatus('success');
      setTimeout(closeModal, 2000);
    } catch (err) {
      alert("Application Failed: " + err.message);
      setSubmitStatus('error');
    }
  };

  const handleCreateJobSubmit = async (e) => {
    e.preventDefault();
    setSubmitStatus('sending');
    try {
      await createJob(jobFormData);
      setSubmitStatus('success');
      setTimeout(() => {
        closeModal();
        loadJobs();
      }, 2000);
    } catch (err) {
      alert("Job Creation Failed: " + err.message);
      setSubmitStatus('error');
    }
  };

  return (
    <div className="dashboard-container">
      <header className="top-bar">
        <div className="brand">
          <div className="logo-icon">🚀</div>
          <div className="brand-text">
            <h1>Unified ATS Integration</h1>
            <p className="subtitle">System Status: {error ? '🔴 Offline' : '🟢 Online'}</p>
          </div>
        </div>
        
        <div style={{display: 'flex', gap: '10px'}}>
            <button className="btn-primary" onClick={openCreateJobModal} style={{margin:0}}>
              + Post New Job
            </button>
            <button className="refresh-btn" onClick={loadJobs} disabled={loading}>
              {loading ? 'Syncing...' : 'Sync Jobs'}
            </button>
        </div>
      </header>

      <main className="content-area">
        {error && <div className="error-banner">{error}</div>}

        <div className="section-header">
          <h2>Active Job Openings</h2>
          <span className="badge-count">{jobs.length} Jobs Found</span>
        </div>

        {loading && jobs.length === 0 ? (
          <div className="loading-state">Fetching data from Zoho...</div>
        ) : (
          <div className="jobs-table-container">
            <table className="jobs-table">
              <thead>
                <tr>
                  <th style={{width: '100px'}}>Unified ID</th>
                  <th>Job Title</th>
                  <th>Location</th>
                  <th style={{textAlign: 'center'}}>Status</th>
                  <th>External URL</th>
                  <th>Description</th>
                  <th style={{textAlign: 'center'}}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((job) => (
                  <tr key={job.id}>
                    {/* ID Truncated in Table (Full ID shown in Modal) */}
                    <td style={{fontFamily: 'monospace', color: '#64748b', fontSize: '0.85rem', verticalAlign: 'middle'}}>
                        <span style={{color: '#cbd5e1'}}>...</span>{job.id.slice(-6)}
                    </td>

                    <td className="job-title-cell" style={{verticalAlign: 'middle'}}>{job.title}</td>
                    
                    {/* Location is now pre-formatted by Backend (City, Country OR Remote) */}
                    <td style={{verticalAlign: 'middle'}}>{job.location}</td>
                    
                    <td style={{verticalAlign: 'middle'}}><span className={`status-pill ${job.status.toLowerCase()}`}>{job.status}</span></td>
                    
                    <td style={{verticalAlign: 'middle'}}>
                        {job.external_url && job.external_url !== '#' ? (
                            <a href={job.external_url} target="_blank" rel="noopener noreferrer" style={{color: '#2563eb', textDecoration: 'none', fontWeight: 500}}>
                                Open Link ↗
                            </a>
                        ) : (
                            <span style={{color: '#94a3b8'}}>--</span>
                        )}
                    </td>

                    <td style={{verticalAlign: 'middle'}}>
                        <button className="btn-secondary" style={{padding: '4px 10px', fontSize: '0.8rem'}} onClick={() => openDescriptionModal(job)}>
                            View Desc
                        </button>
                    </td>

                    <td className="actions-cell" style={{verticalAlign: 'middle'}}>
                      <button className="btn-secondary" onClick={() => openViewAppsModal(job)}>
                        View Apps
                      </button>
                      <button className="btn-primary" onClick={() => openApplyModal(job)}>
                        Apply
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {jobs.length === 0 && !loading && !error && (
              <div className="empty-state" style={{padding: '20px', textAlign: 'center', color: '#64748b'}}>
                No jobs found in the ATS.
              </div>
            )}
          </div>
        )}
      </main>

      {/* --- MODALS --- */}
      {modalMode && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <button className="close-btn" onClick={closeModal}>&times;</button>
            
            {/* 1. DESCRIPTION MODAL */}
            {modalMode === 'VIEW_DESC' && (
              <>
                <div className="modal-header">
                  <h3>Job Description</h3>
                  <p>{activeJob?.title} - {activeJob?.location}</p>
                </div>
                <div style={{lineHeight: '1.6', color: '#334155', maxHeight: '400px', overflowY: 'auto', whiteSpace: 'pre-wrap'}}>
                    {activeJob?.description || "No description provided."}
                </div>
              </>
            )}

            {/* 2. APPLY MODAL (Updated with First/Last Name) */}
            {modalMode === 'APPLY' && (
              <>
                <div className="modal-header">
                  <h3>Apply for {activeJob?.title}</h3>
                  <p>Job ID: {activeJob?.id}</p>
                </div>
                {submitStatus === 'success' ? (
                  <div className="success-message">✅ Application sent to Zoho!</div>
                ) : (
                  <form onSubmit={handleApplySubmit} className="apply-form">
                    {/* SPLIT NAME FIELDS */}
                    <div style={{display: 'flex', gap: '10px'}}>
                        <div className="form-group" style={{flex: 1}}>
                            <label>First Name*</label>
                            <input required value={formData.first_name} onChange={e => setFormData({...formData, first_name: e.target.value})} />
                        </div>
                        <div className="form-group" style={{flex: 1}}>
                            <label>Last Name*</label>
                            <input required value={formData.last_name} onChange={e => setFormData({...formData, last_name: e.target.value})} />
                        </div>
                    </div>

                    <div className="form-group">
                      <label>Email*</label>
                      <input required type="email" value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} />
                    </div>
                    <div className="form-group">
                      <label>Phone*</label>
                      <input required value={formData.phone} onChange={e => setFormData({...formData, phone: e.target.value})} />
                    </div>
                    <div className="form-group">
                      <label>Resume URL (LinkedIn)*</label>
                      <input required value={formData.resume_url} onChange={e => setFormData({...formData, resume_url: e.target.value})} />
                    </div>
                    <button type="submit" className="btn-submit" disabled={submitStatus === 'sending'}>
                      {submitStatus === 'sending' ? 'Sending...' : 'Submit Application'}
                    </button>
                  </form>
                )}
              </>
            )}

            {/* 3. CREATE JOB MODAL (Updated with Remote/City/Country) */}
            {modalMode === 'CREATE_JOB' && (
              <>
                <div className="modal-header">
                  <h3>Post New Job</h3>
                </div>
                {submitStatus === 'success' ? (
                  <div className="success-message">✅ Job Created in Zoho!</div>
                ) : (
                  <form onSubmit={handleCreateJobSubmit} className="apply-form">
                    <div className="form-group">
                      <label>Job Title*</label>
                      <input placeholder="Product Manager" required value={jobFormData.title} onChange={e => setJobFormData({...jobFormData, title: e.target.value})} />
                    </div>
                    
                    {/* REMOTE TOGGLE */}
                    <div className="form-group" style={{display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '15px'}}>
                        <input 
                            type="checkbox" 
                            id="remoteCheck"
                            style={{width: 'auto', margin: 0}}
                            checked={jobFormData.remote} 
                            onChange={e => setJobFormData({...jobFormData, remote: e.target.checked})} 
                        />
                        <label htmlFor="remoteCheck" style={{margin: 0, fontWeight: 'normal'}}>This is a Remote Job</label>
                    </div>

                    {/* CONDITIONAL LOCATION FIELDS */}
                    {!jobFormData.remote && (
                        <div style={{display: 'flex', gap: '10px'}}>
                            <div className="form-group" style={{flex: 1}}>
                                <label>City*</label>
                                <input required={!jobFormData.remote} value={jobFormData.city} onChange={e => setJobFormData({...jobFormData, city: e.target.value})} />
                            </div>
                            <div className="form-group" style={{flex: 1}}>
                                <label>Country*</label>
                                <input required={!jobFormData.remote} value={jobFormData.country} onChange={e => setJobFormData({...jobFormData, country: e.target.value})} />
                            </div>
                        </div>
                    )}

                    <div className="form-group">
                      <label>Description (Min 150 chars)*</label>
                      <textarea 
                        style={{width: '100%', padding: '10px', border: '1px solid #cbd5e1', borderRadius: '8px', minHeight: '100px', resize: 'vertical'}}
                        placeholder="Brief description..." 
                        required 
                        value={jobFormData.description} 
                        onChange={e => setJobFormData({...jobFormData, description: e.target.value})} 
                      />
                    </div>
                    <button type="submit" className="btn-submit" disabled={submitStatus === 'sending'}>
                      {submitStatus === 'sending' ? 'Creating...' : 'Create Job'}
                    </button>
                  </form>
                )}
              </>
            )}

            {/* 4. VIEW APPS MODAL (Updated with Full Job ID & Candidate ID) */}
            {modalMode === 'VIEW_APPS' && (
              <>
                <div className="modal-header">
                  <h3>Applicants for {activeJob?.title}</h3>
                  {/* SHOW FULL JOB ID */}
                  <p>Job ID: {activeJob?.id}</p>
                </div>
                <div className="apps-list">
                  {appLoading ? (
                    <p>Loading applicants...</p>
                  ) : applications.length === 0 ? (
                    <p className="empty-text">No applicants found for this job.</p>
                  ) : (
                    <table className="apps-table">
                      <thead>
                        <tr>
                          {/* ADDED CANDIDATE ID COLUMN */}
                          <th>Candidate ID</th>
                          <th>Name</th>
                          <th>Email</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {applications.map((app) => (
                          <tr key={app.id}>
                            <td style={{fontFamily: 'monospace', color: '#64748b'}}>
                                {app.candidate_id}
                            </td>
                            <td style={{fontWeight: '600'}}>{app.candidate_name}</td>
                            <td>{app.email}</td>
                            <td><span className="status-badge">{app.status}</span></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;