from nc_provision.ncprovision import NcProvision


def provision_cron_job():
    print('Start the CRAMS provision cron job ...')

    nc_provision = NcProvision()
    nc_provision.provision()
    print('Finished the CRAMS provisions')
