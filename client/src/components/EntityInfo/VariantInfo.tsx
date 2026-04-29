import { Box, Typography } from '@mui/material'
import { CategoricalVariant } from '../../models/domain'

type VariantInfoProps = {
  data: CategoricalVariant
}

const VariantInfo = ({ data }: VariantInfoProps) => {
  const displayName = data.name
  const description = 'sldkfjsdf'
  const aliases = ['a', 'b', 'c']
  return (
    <Box id="results-info-container" sx={{ backgroundColor: 'white', padding: 5, borderRadius: 2 }}>
      <Typography variant="h4" mb={2} fontWeight="bold">
        {displayName}
      </Typography>
      <Typography
        variant="h6"
        mb={2}
        fontWeight="bold"
        color="darkgrey"
        display={aliases.length ? 'block' : 'none'}
      >
        Aliases: {aliases.join(', ')}
      </Typography>
      <Typography variant="body1" mb={2} display={description ? 'block' : 'none'}>
        {description}
      </Typography>
    </Box>
  )
}

export default VariantInfo
