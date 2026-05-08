import OverviewPage from '../pages/Docs/About/Overview'
import PublicationsPage from '../pages/Docs/About/Publications'
import SourcesPage from '../pages/Docs/About/Sources'
import TeamPage from '../pages/Docs/About/Team'
import DownloadsPage from '../pages/Docs/DataAndPolicy/Downloads'
import LicensePage from '../pages/Docs/DataAndPolicy/License'
import ContributingPage from '../pages/Docs/GettingInvolved/Contributing'
import ReportingIssuesPage from '../pages/Docs/GettingInvolved/ReportingIssues'
import DataModelPage from '../pages/Docs/Knowledge/DataModel'
import FaqPage from '../pages/Docs/Knowledge/Faq'
import MethodsPage from '../pages/Docs/Knowledge/Methods'

export const docsSections = [
  {
    label: 'About',
    pages: [
      { label: 'Overview', path: '/docs/about/overview', element: <OverviewPage /> },
      { label: 'Team', path: '/docs/about/team', element: <TeamPage /> },
      { label: 'Sources', path: '/docs/about/sources', element: <SourcesPage /> },
      { label: 'Publications', path: '/docs/about/publications', element: <PublicationsPage /> },
    ],
  },
  {
    label: 'Knowledge',
    pages: [
      { label: 'Methods', path: '/docs/knowledge/methods', element: <MethodsPage /> },
      { label: 'Data Model', path: '/docs/knowledge/data_model', element: <DataModelPage /> },
      { label: 'FAQ', path: '/docs/knowledge/faq', element: <FaqPage /> },
    ],
  },
  {
    label: 'Getting Involved',
    pages: [
      {
        label: 'Reporting Issues',
        path: '/docs/getting_involved/reporting_issues',
        element: <ReportingIssuesPage />,
      },
      {
        label: 'Contributing',
        path: '/docs/getting_involved/contributing',
        element: <ContributingPage />,
      },
    ],
  },
  {
    label: 'Data & Policy',
    pages: [
      { label: 'License', path: '/docs/data_policy/license', element: <LicensePage /> },
      { label: 'Downloads', path: '/docs/data_policy/downloads', element: <DownloadsPage /> },
    ],
  },
]
