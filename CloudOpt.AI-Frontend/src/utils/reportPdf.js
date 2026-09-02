import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';

export function generateReportPDF(reportData) {
  if (!reportData) {
    throw new Error('Report data is required to generate PDF');
  }

  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4'
  });

  const pageWidth = doc.internal.pageSize.getWidth(); // 210mm
  const pageHeight = doc.internal.pageSize.getHeight(); // 297mm
  const margin = 14;
  const contentWidth = pageWidth - (margin * 2); // 182mm

  const reportId = reportData.report_id || 'REP-2026-001';
  const reportType = reportData.report_type || 'Monthly';
  const periodText = reportData.formatted_period || `${reportData.period_start || ''} → ${reportData.period_end || ''}`;
  const generatedAt = reportData.generated_at || new Date(reportData.created_at || Date.now()).toLocaleString();
  const optScore = reportData.optimization_score ?? 50;
  const totalSpend = reportData.total_cloud_spend || 'Data unavailable';
  const realizedSavings = typeof reportData.realized_savings === 'number' 
    ? `$${reportData.realized_savings.toFixed(2)}` 
    : '$0.00';
  const avgCpu = `${reportData.average_cpu ?? 0.0}%`;
  const avgRam = `${reportData.average_memory ?? 0.0}%`;
  const avgStorage = `${reportData.average_storage ?? 0.0}%`;
  const peakCpu = `${reportData.peak_cpu ?? reportData.average_cpu ?? 0.0}%`;
  const peakRam = `${reportData.peak_ram ?? reportData.average_memory ?? 0.0}%`;
  const actionsApplied = `${reportData.optimizations_applied ?? 0} Actions`;

  const mlPreds = reportData.ml_predictions || { scale_up: 0, scale_down: 0, no_action: 0 };
  const recs = reportData.recommendations || { total: 0, pending: 0, approved: 0, dismissed: 0 };
  const alerts = reportData.alerts || { active: 0, acknowledged: 0, resolved: 0, critical: 0 };
  const resources = Array.isArray(reportData.resources) ? reportData.resources : [];

  let currentY = 16;

  // ─────────────────────────────────────────────
  // 1. BRAND HEADER & TITLE
  // ─────────────────────────────────────────────
  doc.setFillColor(15, 23, 42); // slate-900
  doc.rect(margin, currentY, contentWidth, 24, 'F');

  // Brand Name
  doc.setTextColor(56, 189, 248); // sky-400
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(16);
  doc.text('CloudOpt.AI', margin + 6, currentY + 9);

  // Subtitle
  doc.setTextColor(226, 232, 240); // slate-200
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(9.5);
  doc.text(`MULTI-CLOUD RESOURCE OPTIMIZATION - ${reportType.toUpperCase()} REPORT`, margin + 6, currentY + 16);

  // Report Badge Right-aligned inside bar
  doc.setFillColor(30, 41, 59);
  doc.roundedRect(pageWidth - margin - 50, currentY + 5, 44, 14, 2, 2, 'F');
  doc.setTextColor(148, 163, 184);
  doc.setFontSize(7);
  doc.text('OPTIMIZATION SCORE', pageWidth - margin - 46, currentY + 9);
  doc.setTextColor(optScore >= 80 ? 16 : optScore >= 60 ? 234 : 239, optScore >= 80 ? 185 : optScore >= 60 ? 179 : 68, optScore >= 80 ? 129 : optScore >= 60 ? 8 : 68);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(11);
  doc.text(`${optScore} / 100`, pageWidth - margin - 46, currentY + 16);

  currentY += 28;

  // Metadata Row
  doc.setFillColor(248, 250, 252);
  doc.setDrawColor(226, 232, 240);
  doc.roundedRect(margin, currentY, contentWidth, 13, 1, 1, 'FD');

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(7.5);
  doc.setTextColor(100, 116, 139);

  doc.text('Report ID:', margin + 4, currentY + 5);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(15, 23, 42);
  doc.text(`${reportId}`, margin + 20, currentY + 5);

  doc.setFont('helvetica', 'normal');
  doc.setTextColor(100, 116, 139);
  doc.text('Report Type:', margin + 62, currentY + 5);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(15, 23, 42);
  doc.text(`${reportType} FinOps Report`, margin + 80, currentY + 5);

  doc.setFont('helvetica', 'normal');
  doc.setTextColor(100, 116, 139);
  doc.text('Generated At:', margin + 4, currentY + 10);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(15, 23, 42);
  doc.text(`${generatedAt}`, margin + 22, currentY + 10);

  doc.setFont('helvetica', 'normal');
  doc.setTextColor(100, 116, 139);
  doc.text('Reporting Period:', margin + 62, currentY + 10);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(15, 23, 42);
  doc.text(`${periodText}`, margin + 86, currentY + 10);

  currentY += 17;

  // ─────────────────────────────────────────────
  // 2. EXECUTIVE SUMMARY
  // ─────────────────────────────────────────────
  doc.setFillColor(241, 245, 249);
  doc.setDrawColor(203, 213, 225);
  doc.roundedRect(margin, currentY, contentWidth, 18, 1, 1, 'FD');

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(8);
  doc.setTextColor(30, 64, 175); // blue-800
  doc.text('EXECUTIVE ANALYSIS & HIGHLIGHTS', margin + 4, currentY + 5.5);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(7.8);
  doc.setTextColor(51, 65, 85);
  const splitSummary = doc.splitTextToSize(reportData.summary_text || 'Multi-cloud optimization analysis from PostgreSQL telemetry.', contentWidth - 8);
  doc.text(splitSummary, margin + 4, currentY + 10.5);

  currentY += 22;

  // ─────────────────────────────────────────────
  // 3. KEY PERFORMANCE INDICATORS (6 Cards)
  // ─────────────────────────────────────────────
  const cardWidth = (contentWidth - 10) / 3;
  const cardHeight = 16;

  const kpis = [
    { label: 'TOTAL CLOUD SPEND', value: totalSpend, sub: 'PostgreSQL telemetry', color: [15, 23, 42] },
    { label: 'REALIZED SAVINGS', value: realizedSavings, sub: `From ${actionsApplied} applied`, color: [16, 185, 129] },
    { label: 'OPTIMIZATIONS APPLIED', value: actionsApplied, sub: 'Human-approved in PostgreSQL', color: [37, 99, 235] },
    { label: reportType === 'Daily' ? 'PEAK FLEET CPU' : 'AVERAGE FLEET CPU', value: reportType === 'Daily' ? peakCpu : avgCpu, sub: reportType === 'Daily' ? `Avg: ${avgCpu}` : 'Across monitored assets', color: [15, 23, 42] },
    { label: reportType === 'Daily' ? 'PEAK FLEET RAM' : 'AVERAGE FLEET RAM', value: reportType === 'Daily' ? peakRam : avgRam, sub: reportType === 'Daily' ? `Avg: ${avgRam}` : 'Across monitored assets', color: [15, 23, 42] },
    { label: 'AVERAGE FLEET STORAGE', value: avgStorage, sub: 'Capacity utilization', color: [15, 23, 42] },
  ];

  kpis.forEach((kpi, idx) => {
    const col = idx % 3;
    const row = Math.floor(idx / 3);
    const x = margin + col * (cardWidth + 5);
    const y = currentY + row * (cardHeight + 4);

    doc.setFillColor(248, 250, 252);
    doc.setDrawColor(226, 232, 240);
    doc.roundedRect(x, y, cardWidth, cardHeight, 1, 1, 'FD');

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(6.5);
    doc.setTextColor(100, 116, 139);
    doc.text(kpi.label, x + 3, y + 4.5);

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(9.5);
    doc.setTextColor(kpi.color[0], kpi.color[1], kpi.color[2]);
    doc.text(String(kpi.value), x + 3, y + 10);

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(6);
    doc.setTextColor(148, 163, 184);
    doc.text(kpi.sub, x + 3, y + 14);
  });

  currentY += (cardHeight * 2) + 10;

  // ─────────────────────────────────────────────
  // 4. INTELLIGENCE SUMMARIES (3 Panels)
  // ─────────────────────────────────────────────
  const panelWidth = (contentWidth - 8) / 3;
  const panelHeight = 22;

  // Panel 1: ML Predictions Summary
  const p1X = margin;
  doc.setFillColor(240, 253, 250);
  doc.setDrawColor(204, 251, 241);
  doc.roundedRect(p1X, currentY, panelWidth, panelHeight, 1, 1, 'FD');
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(7.5);
  doc.setTextColor(13, 148, 136);
  doc.text('ML PREDICTIONS SUMMARY', p1X + 3, currentY + 5);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(7);
  doc.setTextColor(51, 65, 85);
  doc.text(`• Scale Up:  ${mlPreds.scale_up ?? 0}`, p1X + 3, currentY + 10);
  doc.text(`• Scale Down:  ${mlPreds.scale_down ?? 0}`, p1X + 3, currentY + 14.5);
  doc.text(`• No Action:  ${mlPreds.no_action ?? 0}`, p1X + 3, currentY + 19);

  // Panel 2: AI Agent Recommendations Summary
  const p2X = margin + panelWidth + 4;
  doc.setFillColor(238, 242, 255);
  doc.setDrawColor(224, 231, 255);
  doc.roundedRect(p2X, currentY, panelWidth, panelHeight, 1, 1, 'FD');
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(7.5);
  doc.setTextColor(79, 70, 229);
  doc.text('AI AGENT RECOMMENDATIONS', p2X + 3, currentY + 5);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(7);
  doc.setTextColor(51, 65, 85);
  doc.text(`• Pending Review:  ${recs.pending ?? 0}`, p2X + 3, currentY + 10);
  doc.text(`• Approved:  ${recs.approved ?? 0}`, p2X + 3, currentY + 14.5);
  doc.text(`• Dismissed:  ${recs.dismissed ?? 0}`, p2X + 3, currentY + 19);

  // Panel 3: Infrastructure Alerts Summary
  const p3X = margin + (panelWidth * 2) + 8;
  doc.setFillColor(254, 242, 242);
  doc.setDrawColor(254, 226, 226);
  doc.roundedRect(p3X, currentY, panelWidth, panelHeight, 1, 1, 'FD');
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(7.5);
  doc.setTextColor(220, 38, 38);
  doc.text('INFRASTRUCTURE ALERTS', p3X + 3, currentY + 5);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(7);
  doc.setTextColor(51, 65, 85);
  doc.text(`• Active Alerts:  ${alerts.active ?? 0}`, p3X + 3, currentY + 10);
  doc.text(`• Critical Alerts:  ${alerts.critical ?? 0}`, p3X + 3, currentY + 14.5);
  doc.text(`• Resolved:  ${alerts.resolved ?? 0}`, p3X + 3, currentY + 19);

  currentY += panelHeight + 6;

  // ─────────────────────────────────────────────
  // 5. MONITORED FLEET BREAKDOWN TABLE
  // ─────────────────────────────────────────────
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(9);
  doc.setTextColor(15, 23, 42);
  doc.text(`Monitored Fleet Breakdown (${resources.length} Assets - ${reportType} Period)`, margin, currentY + 3);

  currentY += 6;

  const tableHeaders = [
    'Resource ID',
    'Resource Name',
    'Type',
    'CPU %',
    'RAM %',
    'Storage %',
    'Status',
    'Risk Level',
    'ML Prediction',
    'Action Status'
  ];

  const tableRows = resources.map(r => [
    r.resource_id,
    r.name || r.resource_name || `Resource ${r.resource_id}`,
    r.resource_type || 'VM',
    `${r.cpu_usage}%`,
    `${r.memory_usage}%`,
    `${r.storage_usage || 0}%`,
    r.status || 'Normal',
    r.risk_level || 'Low',
    (r.prediction || 'no_action').replace('_', ' ').toUpperCase(),
    (r.recommendation_status || '').toLowerCase() === 'approved' 
      ? 'APPROVED' 
      : (r.recommendation_status || '').toLowerCase() === 'dismissed' 
      ? 'DISMISSED' 
      : (r.recommendation_status || '').toLowerCase() === 'pending' 
      ? 'PENDING REVIEW' 
      : 'OPTIMAL'
  ]);

  autoTable(doc, {
    startY: currentY,
    head: [tableHeaders],
    body: tableRows,
    margin: { left: margin, right: margin, bottom: 18 },
    theme: 'grid',
    styles: {
      fontSize: 7,
      cellPadding: 1.8,
      lineColor: [226, 232, 240],
      lineWidth: 0.2,
      textColor: [30, 41, 59],
      valign: 'middle'
    },
    headStyles: {
      fillColor: [15, 23, 42],
      textColor: [255, 255, 255],
      fontStyle: 'bold',
      fontSize: 7,
      halign: 'left'
    },
    alternateRowStyles: {
      fillColor: [248, 250, 252]
    },
    columnStyles: {
      0: { fontStyle: 'bold', cellWidth: 18 },
      1: { cellWidth: 32 },
      2: { cellWidth: 16 },
      3: { halign: 'right', cellWidth: 13 },
      4: { halign: 'right', cellWidth: 13 },
      5: { halign: 'right', cellWidth: 15 },
      6: { cellWidth: 16 },
      7: { cellWidth: 16 },
      8: { cellWidth: 21 },
      9: { cellWidth: 22, fontStyle: 'bold' }
    },
    didDrawCell: (data) => {
      if (data.section === 'body' && data.column.index === 6) {
        const text = String(data.cell.raw).toLowerCase();
        if (text === 'critical') {
          doc.setTextColor(220, 38, 38);
        } else if (text === 'warning') {
          doc.setTextColor(217, 119, 6);
        } else {
          doc.setTextColor(16, 185, 129);
        }
      }
      if (data.section === 'body' && data.column.index === 9) {
        const text = String(data.cell.raw);
        if (text === 'APPROVED') {
          doc.setTextColor(16, 185, 129);
        } else if (text === 'DISMISSED') {
          doc.setTextColor(100, 116, 139);
        } else if (text === 'PENDING REVIEW') {
          doc.setTextColor(217, 119, 6);
        }
      }
    }
  });

  // ─────────────────────────────────────────────
  // 6. FOOTER ON EVERY PAGE
  // ─────────────────────────────────────────────
  const totalPages = doc.internal.getNumberOfPages();

  for (let pageNum = 1; pageNum <= totalPages; pageNum++) {
    doc.setPage(pageNum);

    doc.setDrawColor(226, 232, 240);
    doc.setLineWidth(0.3);
    doc.line(margin, pageHeight - 12, pageWidth - margin, pageHeight - 12);

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(6.5);
    doc.setTextColor(100, 116, 139);

    // Left footer
    doc.text('CloudOpt.AI - Intelligent Multi-Cloud FinOps & ML Scaling', margin, pageHeight - 7);

    // Center footer
    doc.text(`Generated: ${generatedAt}`, pageWidth / 2, pageHeight - 7, { align: 'center' });

    // Right footer
    doc.text(`Page ${pageNum} of ${totalPages}`, pageWidth - margin, pageHeight - 7, { align: 'right' });
  }

  // ─────────────────────────────────────────────
  // 7. SAVE / DOWNLOAD PDF
  // ─────────────────────────────────────────────
  const cleanReportType = reportType.replace(/[^a-zA-Z0-9]/g, '');
  const cleanReportId = reportId.replace(/[^a-zA-Z0-9-_]/g, '');
  const filename = `CloudOpt_AI_${cleanReportType}_Report_${cleanReportId}.pdf`;

  doc.save(filename);
  return { filename, totalPages };
}
