import React, { useState } from 'react';
import { AlertCircle, CheckCircle2, FileSpreadsheet, Info, Upload } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { ingestionApi, IngestionSummary } from '../api/ingestion';

export const DataImportPage: React.FC = () => {
  const { schoolId } = useAuth();
  const [importType, setImportType] = useState<'attendance' | 'homework' | 'test-scores'>('attendance');
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [summary, setSummary] = useState<IngestionSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !schoolId) {
      setError('Please select a CSV file to upload.');
      return;
    }

    setUploading(true);
    setError(null);
    setSummary(null);

    try {
      let res: IngestionSummary;
      if (importType === 'attendance') {
        res = await ingestionApi.uploadAttendance(schoolId, file);
      } else if (importType === 'homework') {
        res = await ingestionApi.uploadHomework(schoolId, file);
      } else {
        res = await ingestionApi.uploadTestScores(schoolId, file);
      }
      setSummary(res);
    } catch (err: any) {
      setError(err.message || 'CSV Ingestion failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '900px' }}>
      <div>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700 }}>Academic Data Ingestion</h1>
        <p style={{ color: '#64748b', fontSize: '0.9rem' }}>
          Upload attendance, homework, or test score CSV records for school: <strong>{schoolId}</strong>
        </p>
      </div>

      <div className="card">
        <form onSubmit={handleUpload} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {error && (
            <div style={{ background: '#fef2f2', border: '1px solid #fecdd3', color: '#b91c1c', padding: '12px 16px', borderRadius: '8px', fontSize: '0.88rem', display: 'flex', gap: '10px', alignItems: 'center' }}>
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}

          <div className="form-group">
            <label className="form-label">Select Dataset Type</label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
              {[
                { id: 'attendance', title: 'Daily Attendance', cols: 'student_code, date, status' },
                { id: 'homework', title: 'Homework Completion', cols: 'student_code, assignment_id, assignment_date, status' },
                { id: 'test-scores', title: 'Test / Exam Scores', cols: 'student_code, subject, assessment_name, assessment_date, score, max_score' },
              ].map((t) => (
                <div
                  key={t.id}
                  onClick={() => setImportType(t.id as any)}
                  style={{
                    padding: '14px',
                    borderRadius: '10px',
                    border: importType === t.id ? '2px solid #4f46e5' : '1px solid #e2e8f0',
                    background: importType === t.id ? '#eef2ff' : '#ffffff',
                    cursor: 'pointer',
                  }}
                >
                  <h4 style={{ fontSize: '0.9rem', color: importType === t.id ? '#4338ca' : '#0f172a', marginBottom: '4px' }}>
                    {t.title}
                  </h4>
                  <p style={{ fontSize: '0.72rem', color: '#64748b' }}>Expected cols: {t.cols}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Upload CSV File (Max 5 MB)</label>
            <input
              type="file"
              accept=".csv"
              className="form-input"
              onChange={(e) => setFile(e.target.files ? e.target.files[0] : null)}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button type="submit" className="btn btn-primary" disabled={uploading || !file}>
              <Upload size={16} />
              {uploading ? 'Processing CSV...' : 'Start Ingestion'}
            </button>
          </div>
        </form>
      </div>

      {summary && (
        <div className="card" style={{ background: '#f0fdf4', borderColor: '#bbf7d0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#166534', marginBottom: '14px' }}>
            <CheckCircle2 size={20} />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Ingestion Completed Successfully</h3>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '16px' }}>
            <div style={{ background: 'white', padding: '12px', borderRadius: '8px', textAlign: 'center' }}>
              <p style={{ fontSize: '0.75rem', color: '#64748b' }}>Total Rows</p>
              <h4 style={{ fontSize: '1.2rem', fontWeight: 700 }}>{summary.total_rows}</h4>
            </div>
            <div style={{ background: 'white', padding: '12px', borderRadius: '8px', textAlign: 'center' }}>
              <p style={{ fontSize: '0.75rem', color: '#64748b' }}>Ingested</p>
              <h4 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#16a34a' }}>{summary.successful_rows}</h4>
            </div>
            <div style={{ background: 'white', padding: '12px', borderRadius: '8px', textAlign: 'center' }}>
              <p style={{ fontSize: '0.75rem', color: '#64748b' }}>Duplicates</p>
              <h4 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#b45309' }}>{summary.duplicate_rows}</h4>
            </div>
            <div style={{ background: 'white', padding: '12px', borderRadius: '8px', textAlign: 'center' }}>
              <p style={{ fontSize: '0.75rem', color: '#64748b' }}>Errors</p>
              <h4 style={{ fontSize: '1.2rem', fontWeight: 700, color: summary.failed_rows > 0 ? '#b91c1c' : '#475569' }}>
                {summary.failed_rows}
              </h4>
            </div>
          </div>

          <p style={{ fontSize: '0.78rem', color: '#166534' }}>
            Batch ID: <code>{summary.batch_id}</code> (Recorded in Firestore audit log)
          </p>

          {summary.errors.length > 0 && (
            <div style={{ marginTop: '14px', background: '#ffffff', padding: '14px', borderRadius: '8px', border: '1px solid #fecdd3' }}>
              <h5 style={{ fontSize: '0.85rem', color: '#b91c1c', marginBottom: '8px' }}>Row-level Errors:</h5>
              <ul style={{ paddingLeft: '20px', fontSize: '0.8rem', color: '#7f1d1d' }}>
                {summary.errors.map((e, idx) => (
                  <li key={idx}>Row {e.row_number}: {e.error}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
