import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Container,
  Paper,
  Button,
  Typography,
  Box,
  List,
  ListItem,
  ListItemText,
  TextField,
  CircularProgress,
  Chip,
  Grid
} from '@mui/material';

const API_URL = 'http://localhost:5001';

function App() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [parsedData, setParsedData] = useState(null);
  const [resumes, setResumes] = useState([]);
  const [searchSkill, setSearchSkill] = useState('');
  const [jobs, setJobs] = useState([]);
  const [newJob, setNewJob] = useState({ title: '', description: '' });
  const [selectedJob, setSelectedJob] = useState(null);
  const [matchedResumes, setMatchedResumes] = useState([]);
  const [showResumes, setShowResumes] = useState(false);
  const [quickMatchText, setQuickMatchText] = useState('');
  const [showQuickMatch, setShowQuickMatch] = useState(false);

  const fetchJobs = async () => {
    try {
      const response = await axios.get(`${API_URL}/jobs`);
      setJobs(response.data);
    } catch (error) {
      console.error('Error fetching jobs:', error);
    }
  };

  const handleJobSubmit = async () => {
    try {
      await axios.post(`${API_URL}/jobs`, newJob);
      setNewJob({ title: '', description: '' });
      fetchJobs();
    } catch (error) {
      console.error('Error creating job:', error);
      alert('Error creating job');
    }
  };

  const handleQuickMatch = async () => {
    if (!quickMatchText.trim()) return;

    try {
      const response = await axios.post(`${API_URL}/quick-match`, {
        description: quickMatchText
      });
      setMatchedResumes(response.data);
      setShowQuickMatch(true);
    } catch (error) {
      console.error('Error matching resumes:', error);
      alert('Error matching resumes');
    }
  };

  const handleMatchResumes = async (jobId) => {
    try {
      const response = await axios.get(`${API_URL}/jobs/${jobId}/match`);
      setMatchedResumes(response.data);
      setSelectedJob(jobs.find(job => job.id === jobId));
    } catch (error) {
      console.error('Error matching resumes:', error);
      alert('Error matching resumes');
    }
  };

  const fetchResumes = async () => {
    try {
      const response = await axios.get(`${API_URL}/resumes`);
      setResumes(response.data);
      setShowResumes(true);
    } catch (error) {
      console.error('Error fetching resumes:', error);
      alert('Error fetching resumes');
    }
  };

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) {
      alert('Please select a file first');
      return;
    }

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      alert('Please select a PDF file');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setParsedData(response.data);
      fetchResumes(); // Refresh the list
      setFile(null); // Reset file input
      document.getElementById('raised-button-file').value = ''; // Reset file input
    } catch (error) {
      console.error('Error uploading file:', error);
      alert(error.response?.data?.error || 'Error uploading file. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchSkill.trim()) {
      alert('Please enter a skill to search');
      return;
    }

    try {
      const response = await axios.get(`${API_URL}/search?skill=${encodeURIComponent(searchSkill.trim())}`);
      setResumes(response.data);
      setShowResumes(true);
      if (response.data.length === 0) {
        alert('No resumes found with the specified skill');
      }
    } catch (error) {
      console.error('Error searching resumes:', error);
      alert('Error searching resumes. Please try again.');
    }
  };

  useEffect(() => {
    fetchResumes();
    fetchJobs();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Resume Parser</h1>

        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <label
            htmlFor="raised-button-file"
            className="inline-block cursor-pointer bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Select PDF Resume
            <input
              accept=".pdf"
              className="hidden"
              id="raised-button-file"
              type="file"
              onChange={handleFileChange}
            />
          </label>
          <Paper sx={{ p: 2, mb: 2 }}>
            <Typography variant="h6" gutterBottom>
              Quick Resume Match
            </Typography>
            <Box component="form" sx={{ mb: 2 }}>
              <TextField
                fullWidth
                label="Paste Job Description"
                value={quickMatchText}
                onChange={(e) => setQuickMatchText(e.target.value)}
                multiline
                rows={4}
                sx={{ mb: 2 }}
              />
              <Button
                variant="contained"
                onClick={handleQuickMatch}
                disabled={!quickMatchText.trim()}
              >
                Find Matching Resumes
              </Button>
            </Box>
          </Paper>

          {showQuickMatch && matchedResumes.length > 0 && (
            <Paper sx={{ p: 2, mb: 2 }}>
              <Typography variant="h6" gutterBottom>
                Quick Match Results
              </Typography>
              <List>
                {matchedResumes.map((match) => (
                  <ListItem key={match.resume_id} divider>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Typography variant="subtitle1">{match.filename}</Typography>
                          <Chip
                            label={`${match.match_score}% Match`}
                            color={match.match_score > 70 ? 'success' : 'default'}
                            size="small"
                            sx={{ ml: 2 }}
                          />
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2">
                            Email: {match.email}
                          </Typography>
                          <Box sx={{ mt: 1 }}>
                            {match.skills.map((skill) => (
                              <Chip
                                key={skill}
                                label={skill}
                                size="small"
                                sx={{ mr: 1, mb: 1 }}
                              />
                            ))}
                          </Box>
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </Paper>
          )}

          {file && (
            <div className="mt-4">
              <p className="text-gray-600">{file.name}</p>
              <button
                className={`mt-2 bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
                onClick={handleUpload}
                disabled={loading}
              >
                Upload and Parse
              </button>
            </div>
          )}
          {loading && (
            <div className="mt-4">
              <CircularProgress size={24} />
            </div>
          )}
        </div>

        {parsedData && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Parsed Data</h2>
            <div className="space-y-4">
              <div>
                <h3 className="text-gray-600">Email</h3>
                <p className="text-gray-900">{parsedData.email || 'Not found'}</p>
              </div>
              <div>
                <h3 className="text-gray-600">Phone</h3>
                <p className="text-gray-900">{parsedData.phone || 'Not found'}</p>
              </div>
              <div>
                <h3 className="text-gray-600">Skills</h3>
                <div className="flex flex-wrap gap-2 mt-2">
                  {parsedData.skills.map((skill) => (
                    <span
                      key={skill}
                      className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-sm"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
              <div>
                <h3 className="text-gray-600">Work Experience</h3>
                <ul className="mt-2 space-y-2">
                  {parsedData.work_experience.map((exp, index) => (
                    <li key={index} className="text-gray-900">
                      {exp}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="mb-4">
            <h3 className="text-xl font-semibold">Search by Skill</h3>
            <TextField
              label="Enter skill"
              variant="outlined"
              fullWidth
              value={searchSkill}
              onChange={(e) => setSearchSkill(e.target.value)}
            />
            <Button
              variant="contained"
              color="primary"
              sx={{ mt: 2 }}
              onClick={handleSearch}
              disabled={!searchSkill.trim()}
            >
              Search
            </Button>
          </div>

          {showResumes && (
            <Grid container spacing={3}>
              {resumes.map((resume) => (
                <Grid item xs={12} sm={6} md={4} key={resume.resume_id}>
                  <Paper sx={{ p: 2, borderRadius: 2, boxShadow: 1 }}>
                    <Typography variant="h6">{resume.filename}</Typography>
                    <Typography variant="body2">Email: {resume.email}</Typography>
                    <Typography variant="body2">Skills: {resume.skills.join(', ')}</Typography>
                    {/* <Button
                      variant="contained"
                      color="primary"
                      sx={{ mt: 2 }}
                      onClick={() => handleMatchResumes(resume.job_id)}
                    >
                      Match to Job
                    </Button> */}
                  </Paper>
                </Grid>
              ))}
            </Grid>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
